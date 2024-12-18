from celery import shared_task

from .services import order_filler
from .services import order_validator


@shared_task()
def handle_batch_of_request():
    """
    A Celery task that processes a batch of orders from the Redis queue
    and sends notifications for placed and dropped orders.

    This task utilizes the `order_validator` function to validate and process orders.
    After processing, it triggers asynchronous notification tasks for:
    - Successfully placed orders.
    - Dropped orders due to insufficient balance or other issues.

    Steps:
        1. Call `order_validator` to validate and process orders.
        2. If there are successfully placed orders, invoke the `placed_order_notif`
           task.
        3. If there are dropped orders, invoke the `droped_order_notif` task.

    Returns:
        None: This is a background task, so no value is returned.
    """
    placed_order, droped_order = order_validator()

    if placed_order:
        placed_order_notif.delay(placed_order)

    if droped_order:
        droped_order_notif.delay(droped_order)


@shared_task()
def droped_order_notif(order_list: list):
    """
    A pointless task for simulate
    """
    return f"droped order count {len(order_list)}"


@shared_task()
def placed_order_notif(order_list: list):
    """
    A pointless task for simulate
    """
    return f"placed order count {len(order_list)}"


@shared_task()
def accumulate_batch_of_placed_order():
    """
    Processes and fills orders in batches, then notifies the relevant users.

    Uses `order_filler` to fill orders and triggers `filled_order_notif`
    if any users' tokens were updated.

    Returns:
        None
    """
    order_owner_ids = order_filler()
    if order_owner_ids:
        filled_order_notif.delay(order_owner_ids)


@shared_task()
def filled_order_notif(user_ids: list):
    """
    A pointless task for simulate
    """
    return f"filled order count {len(user_ids)}"
