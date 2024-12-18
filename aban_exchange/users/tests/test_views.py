import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestUserSignupApi:
    def setup_method(self):
        self.client = APIClient()

    def test_signup_successful(self):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword123",
        }

        response = self.client.post(reverse("api:users:create"), data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["detail"] == "success"

        user = User.objects.get(username="testuser")
        assert user.email == "testuser@example.com"
        assert user.check_password("testpassword123")

    def test_signup_invalid_data(self):
        data = {"username": "testuser", "password": "testpassword123"}

        response = self.client.post(reverse("api:users:create"), data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_signup_duplicate_username(self):
        User.objects.create_user(
            username="testuser",
            email="initial@example.com",
            password="initialpassword123",  # noqa: S106
        )

        data = {
            "username": "testuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
        }

        response = self.client.post(reverse("api:users:create"), data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data
