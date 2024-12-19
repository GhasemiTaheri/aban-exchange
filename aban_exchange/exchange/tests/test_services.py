from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from redis.exceptions import ConnectionError  # noqa: A004

from aban_exchange.exchange.models import Order
from aban_exchange.exchange.services import order_filler
from aban_exchange.exchange.services import order_validator
from aban_exchange.users.tests.factories import UserFactory
from aban_exchange.utils.exception.system import ServiceUnavailable

User = get_user_model()


@pytest.mark.django_db
@patch("aban_exchange.exchange.services.RedisConnector.get_connection")
def test_order_validator(
    mock_redis_connection,
):
    # Mock Redis connection
    mock_redis = mock_redis_connection.return_value
    mock_redis.lrange.return_value = [
        '{"user_id": "1", "amount": 100, "price": 10}',
        '{"user_id": "2", "amount": 70, "price": 10}',
    ]
    mock_redis.ltrim.return_value = None  # Mock trimming

    UserFactory(id=1, balance=200)
    UserFactory(id=2, balance=50)

    placed_orders, dropped_orders = order_validator()

    # Assert that order was placed for user1 and dropped for user2
    assert len(placed_orders) == 1
    assert (
        User.objects.get(id=1).balance == 100  # noqa: PLR2004
    )  # 200 - 100 (order amount)
    assert len(dropped_orders) == 1


@pytest.mark.django_db
@patch("aban_exchange.exchange.services.RedisConnector.get_connection")
def test_order_validator_redis_error(mock_redis_connection):
    mock_redis = mock_redis_connection.return_value
    mock_redis.lrange.side_effect = ConnectionError("Redis connection error")

    with pytest.raises(ServiceUnavailable, match="Error accessing Redis"):
        order_validator()


@pytest.mark.django_db
def test_order_filler():
    user1 = UserFactory(id=1, token_balance=0)
    user2 = UserFactory(id=2, token_balance=0)

    Order(user=user1, price=10, amount=100).save()
    Order(user=user2, price=10, amount=200).save()

    # Mock token calculation
    with (
        patch("aban_exchange.exchange.services.settings.TOKEN_PRICE", 10),
        patch("aban_exchange.exchange.services.settings.MIN_ORDERS_VALUE", 100),
    ):
        user_ids = order_filler()

    assert user_ids == [user1.id, user2.id]
    assert User.objects.get(id=1).token_balance == 10  # 100 / 10
    assert User.objects.get(id=2).token_balance == 20  # 200 / 10


@pytest.mark.django_db
def test_order_filler_no_valid_orders():
    # Simulate no valid orders
    user_ids = order_filler()

    # Assert that no users are updated when there are no valid orders
    assert user_ids == []
