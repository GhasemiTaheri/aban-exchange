from celery import shared_task

from .services import order_filler
from .services import order_validator


@shared_task()
def handle_batch_of_request():
    placed_order, droped_order = order_validator()

    if placed_order:
        placed_order_notif.delay(placed_order)

    if droped_order:
        droped_order_notif.delay(droped_order)


@shared_task()
def droped_order_notif(order_list: list):
    return f"droped order count {len(order_list)}"


@shared_task()
def placed_order_notif(order_list: list):
    return f"placed order count {len(order_list)}"


@shared_task()
def accumulate_batch_of_placed_order():
    order_owner_ids = order_filler()
    if order_owner_ids:
        filled_order_notif.delay(order_owner_ids)


@shared_task()
def filled_order_notif(user_ids: list):
    return f"filled order count {len(user_ids)}"
