from dataclasses import dataclass


class User:
    """Defines basic User functionalities."""

    def is_authenticated(self) -> bool:
        """Return True if current user is authenticated."""
        raise NotImplementedError

    def is_anonymous(self) -> bool:
        """Return True if current user is not authenticated."""
        raise NotImplementedError

    def domain(self) -> str:
        """Return a domain for this user. The domain must not be specific enough to identify a single user."""
        return 'other'


@dataclass
class AuthenticatedUser(User):
    username: str
    email: str
    fullname: str

    def is_authenticated(self) -> bool:
        return True

    def is_anonymous(self) -> bool:
        return False

    def domain(self) -> str:
        if self.email.lower() == "cara.un@cern.ch" or self.email.endswith('@un.org'):
            return 'UN.org'
        elif self.email.lower().endswith('@cern.ch'):
            return 'CERN'
        else:
            return 'other'


class AnonymousUser(User):
    def is_authenticated(self) -> bool:
        return False

    def is_anonymous(self) -> bool:
        return True
