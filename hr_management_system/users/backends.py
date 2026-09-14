from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to authenticate with email.
    """

    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        """
        Authenticate using email or username.
        """
        try:
            # Try to get user by email if provided, otherwise by username (email field)
            if email:
                user = User.objects.get(email=email)
            elif username:
                # Try both email and username field
                user = User.objects.get(email=username)
            else:
                return None

            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
