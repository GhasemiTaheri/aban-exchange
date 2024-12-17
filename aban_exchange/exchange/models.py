from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import CASCADE
from django.db.models import ForeignKey
from django.db.models import PositiveIntegerField

from aban_exchange.utils.db.models import BaseModel


class BaseOrder(BaseModel):
    user = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        verbose_name="Order owner",
        related_name="%(class)s_related",
        related_query_name="%(class)ss",
    )
    price = PositiveIntegerField(verbose_name="Currency Price")
    amount = PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Amount (USD)",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"user: {self.user_id}, {self.amount} on {self.price}"


class Order(BaseOrder):
    pass


class ArchiveOrder(BaseOrder):
    pass
