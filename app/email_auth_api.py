from __future__ import annotations
from typing import Protocol

import time

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from jose import JWTError
from pydantic import BaseModel, EmailStr, ValidationError

from .jwt import get_jwt_decoder, get_jwt_encoder, JWTDecoder, JWTEncoder


class User(BaseModel):
    """
    User model.
    """

    name: str
    email: EmailStr


class EmailToken(User):
    """
    Auth email token model.
    """

    iat: float
    exp: float

    @classmethod
    def from_user(cls, data: User) -> EmailToken:
        """
        Creates a new token from the given user data.
        """
        now = time.time()
        return cls(name=data.name, email=data.email, iat=now, exp=now + 150)  # Valid for 2.5 minutes.


class UserToken(User):
    """
    User token. The auth cookie, it's expected to be signed / encoded as a JWT if placed in a header.
    """

    created_at: float

    @classmethod
    def from_email_token(cls, token: EmailToken) -> UserToken:
        """
        Creates a new user token from the given email token.
        """
        return cls(name=token.name, email=token.email, created_at=time.time())


class TokenAuthErrorHandler(Protocol):
    """
    User token validation error handler protocol.
    """

    def __call__(self, exception: JWTError | ValidationError, /) -> Response:
        ...


class LoginEmailSender(Protocol):
    """
    Login email sender protocol.
    """

    async def __call__(self, *, user: User, token: str, request_url: str) -> None:
        ...


__USER_TOKEN_COOKIE = "X-User"


def get_user_token(
    user_token_cookie: str | None = Cookie(alias=__USER_TOKEN_COOKIE, default=None),
    decode_jwt: JWTDecoder = Depends(get_jwt_decoder),
) -> UserToken | None:
    """
    Dependency that returns the user token from the current request if there is one.

    Returns:
        The user token that was included in the request or `None` if there was no token or if it was invalid.
    """
    if user_token_cookie is None:
        return None

    try:
        return UserToken(**decode_jwt(user_token_cookie))
    except (JWTError, ValidationError):
        return None


def requires_user_token(token: UserToken | None = Depends(get_user_token)) -> UserToken:
    """
    Dependency that raises an HTTP 401 Unauthorized exception if the request doesn't contain a valid user token.

    Returns:
        The user token that was parsed from the request.

    Raises:
        HTTPException: If the request doesn't contain a valid user token.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing on invalid user token.",
        )

    return token


def make_api(
    *,
    app_redirect_url: str,
    send_login_email: LoginEmailSender,
    token_auth_error_handler: TokenAuthErrorHandler | None,
) -> APIRouter:
    """
    Creates an `APIRouter` with all the routes this module provides.
    """

    api = APIRouter()

    @api.post("/email-login", response_model=User)
    async def request_email_login(
        login_data: User,
        request: Request,
        encode_jwt: JWTEncoder = Depends(get_jwt_encoder),
    ):
        token = EmailToken.from_user(login_data)
        await send_login_email(user=login_data, token=encode_jwt(token.dict()), request_url=str(request.base_url))
        return User(name=token.name, email=token.email)

    @api.get("/email-authorize/{token}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    async def authorize_with_email_token(
        token: str,
        decode_jwt: JWTDecoder = Depends(get_jwt_decoder),
        encode_jwt: JWTEncoder = Depends(get_jwt_encoder),
    ):
        email_token: EmailToken
        try:
            email_token = EmailToken(**decode_jwt(token))
        except (JWTError, ValidationError) as e:
            if token_auth_error_handler:
                return token_auth_error_handler(e)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identity validation failed.",
            )

        user_cookie = UserToken.from_email_token(email_token)

        response = RedirectResponse(app_redirect_url)
        response.set_cookie(__USER_TOKEN_COOKIE, encode_jwt(user_cookie.dict()))
        return response

    @api.get("/email-logout")
    async def email_logout():
        response = RedirectResponse(app_redirect_url)
        response.delete_cookie(__USER_TOKEN_COOKIE)
        return response

    @api.get("/whoami", response_model=User)
    async def whoami(user_token: UserToken = Depends(requires_user_token)):
        return User(name=user_token.name, email=user_token.email)

    return api
