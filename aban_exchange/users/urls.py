from django.urls import include
from django.urls import path

from .views import UserSignupApi

user_url = [
    path(
        "sign-up/",
        UserSignupApi.as_view(),
        name="create",
    ),
]

urlpatterns = [path("user/", include((user_url, "users")))]
