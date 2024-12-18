from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.db.models import PositiveIntegerField


class User(AbstractUser):
    """
    Default custom user model for Aban Exchange.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(blank=True, max_length=255, verbose_name="Name of User")
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    # balance field should be float for commertical use case
    balance = PositiveIntegerField(default=0, verbose_name="Wallet balance")

    # token balance field used for save user assets count
    token_balance = PositiveIntegerField(default=0, verbose_name="Token balance")
