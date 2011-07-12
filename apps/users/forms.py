from django import forms
import django.contrib.auth.forms


class AuthenticationForm(django.contrib.auth.forms.AuthenticationForm):
    """override the authentication form because we use the email address as the
    key to authentication."""
    # allows for using email to log in
    username = forms.CharField(label="Username", max_length=75)
    rememberme = forms.BooleanField(label="Remember me", required=False)
