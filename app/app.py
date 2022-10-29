from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import JWTError
from pydantic import ValidationError

from .chat_api import make_api as make_chat_api
from .email_auth_api import make_api as make_email_auth_api, get_user_token, User, UserToken
from .pages import chat_container, chat_and_connect_scripts, email_login_page, main_page


async def send_login_email(*, user: User, token: str, request_url: str) -> None:
    print(f"LOGIN AT: {request_url}email-authorize/{token}")


def token_auth_error_handler(_exception: JWTError | ValidationError, /) -> HTMLResponse:
    return HTMLResponse(
        str(
            email_login_page(
                email_login_url="/email-login",
                error_message="Incorrect authentication link.",
                error_message_hidden=False,
            )
        )
    )


def register_routes(*, app: FastAPI):
    # -- Register routers and path in order of priority

    @app.get("/")
    async def home(user_token: UserToken | None = Depends(get_user_token)):
        if user_token is None:
            return HTMLResponse(str(email_login_page(email_login_url="/email-login")))

        return HTMLResponse(
            str(
                main_page(
                    chat_room_base_url="/room",
                    user_name=user_token.name,
                    user_email=user_token.email,
                    logout_url="/email-logout",
                )
            )
        )

    @app.get("/room/{room_id}")
    async def chat_room(room_id: str, request: Request, user_token: UserToken | None = Depends(get_user_token)):
        if user_token is None:
            return RedirectResponse("/")

        url = request.base_url
        chat_ws_url = f"ws://{url.hostname}:{url.port}/chat/{room_id}/ws"

        return HTMLResponse(
            str(
                main_page(
                    chat_container(),
                    brand=f"Lounge > Chat > {room_id}",
                    chat_room_base_url="/room",
                    user_name=user_token.name,
                    user_email=user_token.email,
                    logout_url="/email-logout",
                    javascript=chat_and_connect_scripts(chat_ws_url=chat_ws_url),
                )
            )
        )

    app.include_router(
        make_email_auth_api(
            app_redirect_url="/",
            send_login_email=send_login_email,  # type: ignore[arg-type]
            token_auth_error_handler=token_auth_error_handler,
        )
    )
    app.include_router(make_chat_api(), prefix="/chat")

    return  # Skip the rest.


def create_app():
    app = FastAPI()

    register_routes(app=app)

    return app
