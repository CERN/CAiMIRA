from dataclasses import dataclass


class User:
    """Defines basic User functionalities."""

    def is_authenticated(self) -> bool:
        """Return True if current user is authenticated."""
        raise NotImplementedError

    def is_anonymous(self) -> bool:
        """Return True if current user is not authenticated."""
        raise NotImplementedError


@dataclass
class AuthenticatedUser(User):

    username: str
    email: str
    firstname: str
    lastname: str
    fullname: str

    def is_authenticated(self) -> bool:
        return True

    def is_anonymous(self) -> bool:
        return False


class AnonymousUser(User):

    def is_authenticated(self) -> bool:
        return False

    def is_anonymous(self) -> bool:
        return True
