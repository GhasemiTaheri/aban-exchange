from django.conf import settings
from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask


class Command(BaseCommand):
    def _request_handler(self):
        print("Init 'request handler' tasks...")  # noqa: T201

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=settings.REQUEST_HANDLER_INTERVAL,
            period=IntervalSchedule.MICROSECONDS,
        )
        task, created = PeriodicTask.objects.get_or_create(
            interval=schedule,
            name="Validate and place new recieved orders.",
            task="aban_exchange.exchange.tasks.handle_batch_of_request",
        )

        if task:
            print("Done.")  # noqa: T201
        else:
            print("Fail!")  # noqa: T201

    def _order_filler(self):
        print("Init 'order filler' tasks...")  # noqa: T201

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=settings.ORDER_FILLER_INTERVAL,
            period=IntervalSchedule.SECONDS,
        )
        task, created = PeriodicTask.objects.get_or_create(
            interval=schedule,  # we created this above.
            name="Accumulate placed orders and fill them.",
            task="aban_exchange.exchange.tasks.accumulate_batch_of_placed_order",
        )

        if task:
            print("Done.")  # noqa: T201
        else:
            print("Fail!")  # noqa: T201

    def handle(self, *args, **options):
        self._request_handler()
        self._order_filler()
