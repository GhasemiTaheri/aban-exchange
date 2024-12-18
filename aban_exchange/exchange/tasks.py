from celery import shared_task

from .services import order_validator


@shared_task()
def handle_batch_of_request(batch_size=1000):
    order_validator(batch_size)


@shared_task()
def droped_order_notif(user_emails: list):
    pass


@shared_task()
def placed_order_notif(user_emails: list):
    pass
