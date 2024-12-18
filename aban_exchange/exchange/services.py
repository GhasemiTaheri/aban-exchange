import json

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.db.utils import DatabaseError

from aban_exchange.users.models import User
from aban_exchange.utils.exception.system import ServiceUnavailable
from aban_exchange.utils.io.redis_helper import RedisConnector

from .models import ArchiveOrder
from .models import Order


def order_receive(*, user_id: str, amount: int, price: int):
    data = {
        "user_id": user_id,
        "amount": amount,
        "price": price,
    }
    try:
        redis = RedisConnector.get_connection()
        redis.rpush(
            settings.REQUEST_HANDLER_QUEUE_NAME,
            json.dumps(data),
        )
    except Exception:  # noqa: BLE001
        msg = "Error on reciveing order, please try later!"
        raise ServiceUnavailable(msg)  # noqa: B904


def order_validator():
    try:
        redis = RedisConnector.get_connection()
        items = redis.lrange(
            settings.REQUEST_HANDLER_QUEUE_NAME,
            0,
            settings.REQUEST_HANDLER_BATCH_SIZE - 1,
        )
        if not items:
            # placed order list, droped order list
            return [], []

        redis.ltrim(
            settings.REQUEST_HANDLER_QUEUE_NAME,
            settings.REQUEST_HANDLER_BATCH_SIZE,
            -1,
        )
    except Exception as e:  # noqa: BLE001
        msg = f"Error accessing Redis: {e}"
        raise ServiceUnavailable(msg)  # noqa: B904

    raw_orders = []
    order_owner_ids = []
    for item in items:
        data = json.loads(item)
        raw_orders.append(data)
        order_owner_ids.append(data["user_id"])

    try:
        with transaction.atomic():
            order_owner_queryset = (
                User.objects.select_for_update()
                .filter(id__in=order_owner_ids)
                .only(
                    "id",
                    "email",
                    "balance",
                )
            )
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
                    droped_orders.append(order.user_id)

            if user_balance_update:
                User.objects.bulk_update(user_balance_update, ["balance"])
            if placed_orders:
                placed_orders = Order.objects.bulk_create(placed_orders)
    except DatabaseError as e:
        droped_orders.extend(placed_orders)
        placed_orders = []

        msg = f"Database transaction failed: {e}"
        raise ServiceUnavailable(msg)  # noqa: B904

    return [i.id for i in placed_orders], droped_orders


def order_filler():
    queryset = Order.objects.filter(price=settings.TOKEN_PRICE)
    total_value = queryset.aggregate(
        total_value=Sum(
            "amount",
            default=0,
        ),
    ).get("total_value")

    if total_value >= settings.MIN_ORDERS_VALUE:
        updated_user_token = []
        archive_order = []
        token_group_by_user = {}

        with transaction.atomic():
            for order in queryset.select_related("user"):
                token_group_by_user[order.user.id] = token_group_by_user.get(
                    order.user.id, 0
                ) + (order.amount // settings.TOKEN_PRICE)
                archive_order.append(order)
                updated_user_token.append(order.user)

            for user in updated_user_token:
                user.token_balance += token_group_by_user.get(user.id)

            ArchiveOrder.objects.bulk_create(archive_order)
            User.objects.bulk_update(updated_user_token, ["token_balance"])
            queryset.delete()

        return [user.id for user in updated_user_token]

    return []
