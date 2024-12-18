from .models import User


def user_create(*, username: str, email: str, password: str):
    """
    Creates a new user with the given username, email, and password.

    This function uses Django's `create_user` method to create a new user in the
    database. It ensures that the password is properly hashed and stored securely.

    Args:
        username (str): The username for the new user.
        email (str): The email address for the new user.
        password (str): The password for the new user.

    Returns:
        User: The newly created user instance.

    Raises:
        IntegrityError: If the username or email is not unique.
        ValidationError: If the provided data is invalid.
    """
    return User.objects.create_user(username=username, email=email, password=password)
