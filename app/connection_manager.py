from typing import Hashable, Protocol

import asyncio

from fastapi import WebSocket


Message = str


class ConnectionManager(Protocol):
    def __len__(self) -> int:
        """
        The number of active connections.
        """
        ...

    @property
    def is_empty(self) -> bool:
        """
        Whether the connection manager is empty, i.e. it has no connections.
        """
        return len(self) == 0

    async def connect(self, connection: WebSocket) -> None:
        """
        Registers the given connection.

        Arguments:
            connection: The connection that should be registered.
        """
        ...

    def disconnect(self, connection: WebSocket) -> None:
        """
        Unregisters the given connection.

        Arguments:
            connection: The connection should be unregistered..
        """
        ...

    async def send_group_message(self, *, message: Message, connections: list[WebSocket]) -> None:
        """
        Sends the given message to the given connections.

        Arguments:
            message: The message to send.
            connections: The connections the message should be sent to.
        """
        ...

    async def send_personal_message(self, *, message: Message, connection: WebSocket) -> None:
        """
        Sends the given message to the given connection.

        Arguments:
            message: The message to send.
            connection: The connection the message should be sent to.
        """
        ...

    async def broadcast(self, *, message: Message, skip: list[WebSocket] = []) -> None:
        """
        Sends to given message to every connection except the ones in `skip`.

        Arguments:
            message: The message to broadcast.
            skip: The connections that should be overlooked.
        """
        ...


class WebSocketConnectionManager(ConnectionManager):
    """
    Default web socket connection manager implementation.

    All messages are ultimately sent using the `_send_message()` method to make it easy
    to hook into the message sending process.
    """

    __slots__ = ("_active_connections",)

    def __init__(self):
        """
        Initialization.
        """
        self._active_connections: list[WebSocket] = []

    def __len__(self) -> int:
        """
        Inherited.
        """
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket):
        """
        Inherited.
        """
        await websocket.accept()
        self._active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Inherited.
        """
        self._active_connections.remove(websocket)

    async def _send_message(self, *, message: Message, connection: WebSocket) -> None:
        """
        Corutine that sends the given message on the given connection.

        All other messaging methods must call this one to actually send a message. The goal
        is to make it easy to hook into the message sending process.

        Arguments:
            message: The message to send.
        """
        await connection.send_text(message)

    async def send_group_message(self, *, message: Message, connections: list[WebSocket]) -> None:
        """
        Inherited.
        """
        await asyncio.gather(*(self._send_message(message=message, connection=conn) for conn in connections))

    async def send_personal_message(self, *, message: Message, connection: WebSocket):
        """
        Inherited.
        """
        await self._send_message(message=message, connection=connection)

    async def broadcast(self, *, message: Message, skip: list[WebSocket] = []):
        """
        Inherited.
        """
        await asyncio.gather(
            *(
                self._send_message(message=message, connection=conn)
                for conn in self._active_connections
                if conn not in skip
            )
        )


ConnectionManagerRegistryKey = Hashable  # Including None


class ConnectionManagerFactory(Protocol):
    """
    Connection manager factory protocol.
    """

    def __call__(self, key: ConnectionManagerRegistryKey) -> ConnectionManager:
        ...


class ConnectionManagerRegistry:
    """
    Registry that associates connection managers with unique keys.
    """

    __slots__ = (
        "_connection_managers",
        "_make_connection_manager",
    )

    def __init__(self, *, connection_manager_factory: ConnectionManagerFactory) -> None:
        """
        Initialization.

        Arguments:
            connection_manager_factory: The factory the registry will use to create new connection managers.
        """
        self._make_connection_manager: ConnectionManagerFactory = connection_manager_factory
        self._connection_managers: dict[ConnectionManagerRegistryKey, ConnectionManager] = {}

    def cleanup(self) -> list[ConnectionManagerRegistryKey]:
        """
        Removes all empty connection managers from the registry and returns the corresponding keys.
        """
        result = [key for key, value in self._connection_managers.items() if value.is_empty]

        for key in result:
            del self._connection_managers[key]

        return result

    def ensure_connection_manager(self, key: ConnectionManagerRegistryKey) -> ConnectionManager:
        """
        Returns the connection manager that is registered with the given key, creating and registering
        a new one if no such connection manager existed.

        Arguments:
            key: The connection manager's key.
        """
        if key not in self._connection_managers:
            self._connection_managers[key] = self._make_connection_manager(key)

        return self._connection_managers[key]

    def get_connection_manager(self, key: ConnectionManagerRegistryKey) -> ConnectionManager | None:
        """
        Returns the connection manager that is registered with the given key, if such a connection manager exists.

        Arguments:
            key: The connection manager's key.
        """
        return self._connection_managers.get(key, None)

    def notify_disconnect(self, key: ConnectionManagerRegistryKey) -> None:
        """
        Notifies the registry that a client disconnected from the connection manager that is
        registered with the given key.

        The main task of this method is to clean up empty connection managers.

        Arguments:
            key: The key of the connection manager from which a client disconnected.
        """
        conn_manager = self._connection_managers.get(key, None)
        if conn_manager and conn_manager.is_empty:
            del self._connection_managers[key]
