from __future__ import annotations
from typing import Protocol

from asyncio import gather
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from .connection_manager import ConnectionManagerRegistry, WebSocketConnectionManager
from .email_auth_api import User, requires_user_token

RoomId = str


def make_message(msg: str, /, *, user: User, self: bool = False) -> str:
    """
    Creates a JSON message from the given data.

    Arguments:
        msg: Message text.
        user: The current user.
        from_self: Whether the message is sent by the current user.
    """
    return json.dumps({"user": {"name": user.name, "email": user.email, "self": self}, "message": msg})


def make_api() -> APIRouter:
    """
    Creates an `APIRouter` with all the routes this module provides.
    """

    api = APIRouter()

    connection_manager_registry = ConnectionManagerRegistry(
        connection_manager_factory=lambda _key: WebSocketConnectionManager()
    )

    @api.websocket("/{room}/ws")
    async def chat(
        room: str,
        connection: WebSocket,
        user: User = Depends(requires_user_token),
    ):
        conn_manager = connection_manager_registry.ensure_connection_manager(room)

        await conn_manager.connect(connection)

        await gather(
            # Announce the newly joined chat member.
            conn_manager.broadcast(
                message=make_message(f"{user.name} ({user.email}) joined the chat.", user=user), skip=[connection]
            ),
            # Send welcome message.
            conn_manager.send_personal_message(
                message=make_message(f"Welcome to the chat {user.name} ({user.email}).", user=user, self=True),
                connection=connection,
            ),
        )

        try:
            while True:  # Start listening for messages.
                data = await connection.receive_text()
                await gather(
                    conn_manager.send_personal_message(
                        message=make_message(data, user=user, self=True), connection=connection
                    ),
                    conn_manager.broadcast(message=make_message(data, user=user), skip=[connection]),
                )
        except WebSocketDisconnect:
            conn_manager.disconnect(connection)
            await conn_manager.broadcast(
                message=make_message(f"{user.name} ({user.email}) left the chat.", user=user)
            )
            connection_manager_registry.notify_disconnect(room)

    return api
