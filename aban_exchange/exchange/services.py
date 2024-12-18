import json

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.transaction import atomic
from django.utils.timezone import datetime

from aban_exchange.users.models import User
from aban_exchange.utils.exception.system import ServiceUnavailable
from aban_exchange.utils.io.redis_helper import RedisConnector

from .models import Order


async def order_receive(*, user_id: str, amount: int, price: int):
    data = {
        "user_id": user_id,
        "amount": amount,
        "price": price,
        "recieved_at": datetime.now(),
    }
    try:
        redis = await sync_to_async(RedisConnector.get_connection())
        await sync_to_async(
            redis.rpush(
                settings.REQUEST_HANDLER_QUEUE_NAME,
                json.dumps(data),
            ),
        )
    except Exception:
        raise ServiceUnavailable()


def order_validator():
    try:
        redis = RedisConnector.get_connection()
        items = redis.lrange(
            settings.REQUEST_HANDLER_QUEUE_NAME,
            0,
            settings.REQUEST_HANDLER_BATCH_SIZE - 1,
        )
        if items:
            redis.ltrim(
                settings.REQUEST_HANDLER_QUEUE_NAME,
                settings.REQUEST_HANDLER_BATCH_SIZE,
                -1,
            )
        else:
            # success count, droped_count
            return 0, 0
    except Exception:
        raise ServiceUnavailable()

    raw_orders = []
    order_owner_ids = []
    for item in items:
        data = json.loads(item)
        raw_orders.append(data)
        order_owner_ids.append(data["user_id"])

    order_owner_queryset = User.objects.only(
        "id",
        "email",
        "balance",
    ).filter(id__in=order_owner_ids)[:]  # force filter to execute

    user_balance_update = []
    placed_orders = []
    droped_orders = []

    for _ in raw_orders:
        order = Order(
            user_id=_["user_id"],
            price=_["price"],
            amount=_["amount"],
        )
        order_owner = order_owner_queryset.get(id=order.user_id)

        if order_owner.balance >= order.amount:
            order_owner.balance -= order.amount
            user_balance_update.append(order_owner)
            placed_orders.append(order)
        else:
            droped_orders.append(order)

    with atomic:
        User.objects.bulk_update(user_balance_update, ["balance"])
        Order.objects.bulk_create(placed_orders)

    return len(placed_orders), len(droped_orders)
