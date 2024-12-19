import pytest

from aban_exchange.users.models import User
from aban_exchange.users.tests.factories import UserFactory


@pytest.fixture
def user(db) -> User:
    return UserFactory(password="password123")  # noqa: S106
