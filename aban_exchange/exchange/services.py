from asgiref.sync import sync_to_async
from django.conf import REDIS_URL
from redis import Redis


async def order_receive(*, user_auth_token: str, amount: int, price: int):
    data = {
        "user": user_auth_token,
        "amount": amount,
        "price": price,
    }
    try:
        redis = await sync_to_async(Redis.from_url(REDIS_URL))
        await sync_to_async(redis.rpush("recieve_order_queue", data))
    except:
        # TODO: complete this section
        pass
