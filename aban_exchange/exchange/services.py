import json

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.db.utils import DatabaseError
from django.utils.timezone import datetime

from aban_exchange.users.models import User
from aban_exchange.utils.exception.system import ServiceUnavailable
from aban_exchange.utils.io.redis_helper import RedisConnector

from .models import Order


def order_receive(*, user_id: str, amount: int, price: int):
    data = {
        "user_id": user_id,
        "amount": amount,
        "price": price,
        "recieved_at": datetime.now(),
    }
    try:
        redis = RedisConnector.get_connection()
        redis.rpush(
            settings.REQUEST_HANDLER_QUEUE_NAME,
            json.dumps(data),
        )
    except Exception:
        raise ServiceUnavailable()


async def order_validator():
    try:
        redis = await RedisConnector.aget_connection()
        items = await redis.lrange(
            settings.REQUEST_HANDLER_QUEUE_NAME,
            0,
            settings.REQUEST_HANDLER_BATCH_SIZE - 1,
        )
        if not items:
            # placed order list, droped order list
            return [], []

        await redis.ltrim(
            settings.REQUEST_HANDLER_QUEUE_NAME,
            settings.REQUEST_HANDLER_BATCH_SIZE,
            -1,
        )
    except Exception as e:  # noqa: BLE001
        raise ServiceUnavailable(f"Error accessing Redis: {e}")  # noqa: B904, EM102, TRY003

    raw_orders = []
    order_owner_ids = []
    for item in items:
        data = json.loads(item)
        raw_orders.append(data)
        order_owner_ids.append(data["user_id"])

    order_owner_queryset = await sync_to_async(
        lambda: User.objects.filter(id__in=order_owner_ids).only(
            "id",
            "email",
            "balance",
        ),
    )()

    order_owner_map = {user.id: user for user in order_owner_queryset}

    user_balance_update = []
    placed_orders = []
    droped_orders = []

    for _ in raw_orders:
        order = Order(
            user_id=_["user_id"],
            price=_["price"],
            amount=_["amount"],
        )
        order_owner = order_owner_map.get(order.user_id)

        if order_owner.balance >= order.amount:
            order_owner.balance -= order.amount
            user_balance_update.append(order_owner)
            placed_orders.append(order)
        else:
            droped_orders.append(order)

    try:
        async with transaction.atomic():
            if user_balance_update:
                await sync_to_async(
                    lambda: User.objects.bulk_update(user_balance_update, ["balance"]),
                )()
            if placed_orders:
                await sync_to_async(lambda: Order.objects.bulk_create(placed_orders))()
    except DatabaseError as e:
        droped_orders.extend(placed_orders)
        placed_orders = []

        msg = f"Database transaction failed: {e}"
        raise ServiceUnavailable(msg)  # noqa: B904

    return placed_orders, droped_orders
