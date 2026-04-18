from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserInfo:
    sub: str
    name: str
    email: str
    email_verified: bool = False
