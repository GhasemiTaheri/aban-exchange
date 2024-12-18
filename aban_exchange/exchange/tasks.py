from celery import shared_task

from .services import order_validator


@shared_task()
async def handle_batch_of_request():
    placed_order, droped_order = await order_validator()

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
