from dataclasses import dataclass


@dataclass
class RegisterRequest:
    username: str
    password: str
    email: str


@dataclass
class RegisterResponse:
    id: int
    access_token: str
    refresh_token: str


@dataclass
class LoginRequest:
    username: str
    password: str


@dataclass
class LoginResponse:
    id: int
    access_token: str
    refresh_token: str


@dataclass
class RefreshResponse:
    access_token: str
    refresh_token: str
