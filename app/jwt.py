from typing import Protocol
from functools import partial

from fastapi import Depends
from jose import jwt
from jose.constants import ALGORITHMS

from .settings import get_settings, Settings


class JWTDecoder(Protocol):
    """
    JWT decoder protocol.
    """

    def __call__(self, token: str | bytes, algorithms: list[str] | None = None) -> dict:
        ...


class JWTEncoder(Protocol):
    """
    JWT encoder protocol.
    """

    def __call__(self, claims: dict) -> str:
        ...


def get_jwt_decoder(settings: Settings = Depends(get_settings)) -> JWTDecoder:
    """
    Returns a preconfigured JWT decoder.

    FastAPI dependency.
    """

    def decoder(token: str | bytes, algorithms: list[str] | None = None) -> dict:
        return jwt.decode(
            token, key=settings.jwt_key, algorithms=[ALGORITHMS.HS256] if algorithms is None else algorithms
        )

    return decoder


def get_jwt_encoder(settings: Settings = Depends(get_settings)) -> JWTEncoder:
    """
    Returns a preconfigured JWT encoder.

    FastAPI dependency.
    """
    return partial(jwt.encode, key=settings.jwt_key, algorithm=ALGORITHMS.HS256)
