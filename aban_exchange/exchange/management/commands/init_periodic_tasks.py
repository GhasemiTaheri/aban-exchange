from django.conf import settings
from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Please wait...")  # noqa: T201

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=settings.REQUEST_HANDLER_INTERVAL,
            period=IntervalSchedule.MICROSECONDS,
        )
        task, created = PeriodicTask.objects.get_or_create(
            interval=schedule,  # we created this above.
            name="Validate and placed new recieved order",  # simply describes this periodic task.
            task="aban_exchange.exchange.tasks.handle_batch_of_request",  # name of task.
        )

        if task:
            print("Done.")  # noqa: T201
        else:
            print("Fail!")  # noqa: T201
