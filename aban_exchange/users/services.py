from .models import User


def user_create(*, username: str, email: str, password: str):
    return User.objects.create_user(username=username, email=email, password=password)
