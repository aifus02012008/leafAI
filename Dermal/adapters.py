from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Automatically link existing local accounts to social accounts based on email.
        This prevents the "account with this email already exists" error or signup form.
        """
        # If the social account is already connected, do nothing
        if sociallogin.is_existing:
            return

        # Check if we have an email
        email = sociallogin.account.extra_data.get('email')
        if not email:
            return

        # Look for an existing user with this email
        try:
            user = User.objects.get(email__iexact=email)
            # Link the social account to the existing user
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
