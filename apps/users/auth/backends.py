from django.contrib.auth.models import User
from django_auth_ldap.backend import LDAPBackend

class MozillaLDAPBackend(LDAPBackend):
    """Overriding this class so that I can transform emails to usernames.

    At Mozilla we use email addresses as the username but in django I want,
    for example:
        INPUT:
            username -> pbengtsson@mozilla.com
        OUTPUT:
            username -> pbengtsson
            email -> pbengtsson@mozilla.com

    I can map (in settings.AUTH_LDAP_USER_ATTR_MAP):
        'username' -> 'uid'
        and
        'email -> 'mail

    But that means that the second time a user logs in, it's not going to
    find a username that is 'pbengtsson@mozilla.com' so it'll go ahead and
    create it again and you'll end up with duplicates once the attribute
    conversion is done.

    The other thing that this backend accomplishes is to change username
    entirely. Suppose, for example, that your mozilla LDAP email is
    'pbengtsson@mozilla.com' but you prefer your own custom alias of
    'peterbe'. What it does then, is looking at existing users that match
    the *email address* and returns the username for that one.
    """

    def ldap_to_django_username(self, username):
        try:
            return User.objects.get(email=username).username
        except User.DoesNotExist:
            return username.split('@')[0]
