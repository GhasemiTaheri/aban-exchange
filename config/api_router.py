from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from aban_exchange.exchange.urls import urlpatterns as exchange_url
from aban_exchange.users.urls import urlpatterns as user_url

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


app_name = "api"
urlpatterns = [
    *router.urls,
    *user_url,
    *exchange_url,
]
