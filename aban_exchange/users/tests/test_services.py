import pytest
from django.db import IntegrityError

from aban_exchange.users.services import user_create


@pytest.mark.django_db
class TestUserCreate:
    def test_user_create_successful(self):
        username = "newuser"
        email = "newuser@example.com"
        password = "newpassword123"

        user = user_create(username=username, email=email, password=password)

        assert user.username == username
        assert user.email == email
        assert user.check_password(
            password,
        )
        assert user.id is not None

    def test_user_create_duplicate_username(self):
        username = "existinguser"
        email = "existing@example.com"
        password = "password123"

        user_create(username=username, email=email, password=password)

        with pytest.raises(IntegrityError):
            user_create(
                username=username, email="another@example.com", password="password456"
            )
