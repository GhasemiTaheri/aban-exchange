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
    """
    Adds an order to the Redis queue for asynchronous processing.

    This function packages the given `user_id`, `amount`, and `price` into a dictionary,
    serializes it to JSON, and pushes it to a Redis list (queue).
    The queue name is defined in `settings.REQUEST_HANDLER_QUEUE_NAME`.

    Args:
        user_id (str): The unique identifier of the user placing the order.
        amount (int): The quantity or amount of the order.
        price (int): The price of the order.

    Raises:
        ServiceUnavailable: If an error occurs while connecting to Redis or pushing data
        to the queue.
    """

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
    """
    Validates and processes a batch of orders from the Redis queue.

    This function retrieves a batch of raw orders from a Redis queue, validates them
    against the users' balances, and processes them in a transactional manner. Valid
    orders are placed, users' balances are updated, and invalid orders are dropped.

    Returns:
        tuple: A tuple containing:
            - A list of IDs of successfully placed orders.
            - A list of user IDs of dropped orders for notify them in another time.

    Raises:
        ServiceUnavailable:
            - If there is an issue with accessing Redis.
            - If there is a failure in the database transaction.

    Steps:
        1. Retrieve a batch of orders from the Redis queue.
        2. Parse and prepare raw orders and their associated user IDs.
        3. Validate and process orders in a database transaction:
            - Deduct balance for valid orders.
            - Save valid orders in the database.
            - Drop invalid orders (insufficient balance).
        4. Handle transaction failures:
            - Move placed orders to the dropped list if the transaction fails.
    """

    try:
        redis = RedisConnector.get_connection()
        items = redis.lrange(
            settings.REQUEST_HANDLER_QUEUE_NAME,
            0,
            settings.REQUEST_HANDLER_BATCH_SIZE - 1,
        )
        if not items:
            # Return empty lists if no items are found in the queue
            return [], []

        # Trim the Redis queue to remove the processed batch
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
        # Deserialize each order and collect user IDs for further processing
        data = json.loads(item)
        raw_orders.append(data)
        order_owner_ids.append(data["user_id"])

    try:
        with transaction.atomic():
            # Retrieve users with their balances in a locked state for transaction safety  # noqa: E501
            order_owner_queryset = (
                User.objects.select_for_update()
                .filter(id__in=order_owner_ids)
                .only(
                    "id",
                    "email",
                    "balance",
                )
            )

            # Map users by their IDs for quick lookup
            order_owner_map = {user.id: user for user in order_owner_queryset}
            user_balance_update = []  # Users whose balances will be updated
            placed_orders = []
            droped_orders = []

            for _ in raw_orders:
                order = Order(
                    user_id=_["user_id"],
                    price=_["price"],
                    amount=_["amount"],
                )
                order_owner = order_owner_map.get(int(order.user_id))

                # Check if the user has enough balance to place the order
                if order_owner.balance >= order.amount:
                    order_owner.balance -= order.amount
                    user_balance_update.append(order_owner)
                    placed_orders.append(order)
                else:
                    droped_orders.append(order.user_id)

            # Update user balances and save placed orders in bulk to decrease IO operation  # noqa: E501
            if user_balance_update:
                User.objects.bulk_update(user_balance_update, ["balance"])
            if placed_orders:
                placed_orders = Order.objects.bulk_create(placed_orders)

    except DatabaseError as e:
        # If the transaction fails, move placed orders to the dropped list
        droped_orders.extend(placed_orders)
        placed_orders = []

        msg = f"Database transaction failed: {e}"
        raise ServiceUnavailable(msg)  # noqa: B904

    # Return the IDs of placed orders and dropped orders
    return [i.id for i in placed_orders], droped_orders


def order_filler():
    """
    Processes orders that match a specific price, updates user token balances,
    and archives the orders in bulk.

    This function checks if the total value of orders with a price matching
    `settings.TOKEN_PRICE` meets or exceeds a minimum threshold (`settings.MIN_ORDERS_VALUE`).
    If so, it calculates the number of tokens to add to each user's balance based on their
    orders, archives the orders, and updates the users' balances within a database transaction.

    Returns:
        list: A list of user IDs whose token balances were updated.

    Returns an empty list if the total value of orders is below the minimum threshold.

    Steps:
        1. Retrieve and aggregate orders with the matching price.
        2. Check if the total value of these orders meets the minimum threshold.
        3. If valid, process the orders:
            - Group token amounts by user.
            - Update user balances with the calculated tokens.
            - Archive the processed orders.
            - Delete the processed orders from the database.
        4. Return the list of updated user IDs.

    Raises:
        ServiceUnavailable:
            - If there is a failure in the database transaction.
    """

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

        # Dictionary to group tokens count by user ID,
        # if we don't use this mechanism we need to update field in db by each order
        # placed by a specific user
        # example: if user 'A' placed 2 order with volume 10$ on price 5
        # he must recieve 4 tokens.
        # well, if we don't use this algorithm he/she just recieves 2 tokens
        token_group_by_user = {}

        try:
            with transaction.atomic():
                for order in queryset.select_related("user"):
                    # Calculate tokens for each user and accumulate them
                    token_group_by_user[order.user.id] = token_group_by_user.get(
                        order.user.id,
                        0,
                    ) + (order.amount // settings.TOKEN_PRICE)
                    archive_order.append(order)
                    updated_user_token.append(order.user)

                # Update user token balances in memory
                for user in updated_user_token:
                    user.token_balance += token_group_by_user.get(user.id)

                User.objects.bulk_update(updated_user_token, ["token_balance"])

                # Archive and delete the processed orders from the database,
                # because we need the number of records in the table to be optimized
                # for faster access
                ArchiveOrder.objects.bulk_create(archive_order)
                queryset.delete()

            return [user.id for user in updated_user_token]
        except DatabaseError as e:
            msg = f"Database transaction failed: {e}"
            raise ServiceUnavailable(msg)  # noqa: B904

    return []
