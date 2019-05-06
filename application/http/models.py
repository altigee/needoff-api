from dataclasses import dataclass


@dataclass
class HttpError:
    error: str


@dataclass
class HttpMessage:
    message: str
