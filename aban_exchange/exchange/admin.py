from django.contrib import admin

from .models import ArchiveOrder
from .models import Order

# Register your models here.
admin.site.register(Order)
admin.site.register(ArchiveOrder)