from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestOrderCreateApi:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    def get_access_token(self, api_client, user):
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": user.username, "password": "password123"},
        )
        assert response.status_code == status.HTTP_200_OK
        return response.data["access"]

    def test_order_create_successful(self, api_client, user):
        access_token = self.get_access_token(api_client, user)
        order_data = {
            "amount": 10,
            "price": 100,
        }

        # Mocking the order_receive function to avoid actual Redis calls
        with patch("aban_exchange.exchange.views.order_receive") as mock_order_receive:
            mock_order_receive.return_value = None

            response = api_client.post(
                reverse("api:orders:create"),
                order_data,
                HTTP_AUTHORIZATION=f"Bearer {access_token}",
            )

            assert response.status_code == status.HTTP_201_CREATED
            assert (
                response.data["detail"]
                == "we recieve your order successfully. we notice you with email!"
            )
            mock_order_receive.assert_called_once_with(
                user_id=user.id,
                amount=10,
                price=100,
            )

    def test_order_create_invalid_data(self, api_client, user):
        access_token = self.get_access_token(api_client, user)
        order_data = {
            "amount": -1,  # Invalid amount
            "price": 100,
        }

        response = api_client.post(
            reverse("api:orders:create"),
            order_data,
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "amount" in response.data

    def test_order_create_unauthenticated(self, api_client):
        order_data = {
            "amount": 10,
            "price": 100,
        }
        response = api_client.post(reverse("api:orders:create"), order_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
