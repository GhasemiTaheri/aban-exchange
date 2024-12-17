from celery import shared_task
from django.conf import settings
from redis import Redis


@shared_task()
def handle_batch_of_request():
    try:
        redis_db = Redis.from_url(settings.REDIS_URL)
        redis_db.rpop("recieve_order_queue")
    except:
        pass

    return "Im worked"
