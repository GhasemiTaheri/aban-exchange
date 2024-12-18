from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import PROTECT
from django.db.models import ForeignKey
from django.db.models import Index
from django.db.models import PositiveIntegerField

from aban_exchange.utils.db.models import BaseModel


class BaseOrder(BaseModel):
    user = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
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
        return f"user: {self.user_id}, {self.amount}$ on price {self.price}"


class Order(BaseOrder):
    class Meta:
        indexes = [
            # we index price field because we aggrigate all order by this field.
            Index(fields=["price"]),
        ]


class ArchiveOrder(BaseOrder):
    pass
