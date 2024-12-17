from django.urls import include
from django.urls import path

from .views import OrderCreateApi

order_url = [
    path(
        "create/",
        OrderCreateApi.as_view(),
        name="create",
    ),
]

urlpatterns = [path("order/", include((order_url, "orders")))]
