from django import forms
from django.contrib.auth.models import User
import django.contrib.auth.forms


class AuthenticationForm(django.contrib.auth.forms.AuthenticationForm):
    """override the authentication form because we use the email address as the
    key to authentication."""
    # allows for using email to log in
    username = forms.CharField(label="Username", max_length=75)
    rememberme = forms.BooleanField(label="Remember me", required=False)

class SettingsForm(forms.Form):
    username = forms.CharField(label="Username", max_length=75)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SettingsForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        if (User.objects
            .filter(username__iexact=value)
            .exclude(pk=self.user.pk)
            .exists()):
            raise forms.ValidationError("Username already used by someone else")
        return value
