"""
Use this script once to import a list of users by their email address.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from utils import get_user_name
from .ldap_lookup import fetch_user_details

class Command(BaseCommand):  #pragma: no cover
    help = "Imports a bunch of users that can be found in LDAP"
    args = '[fileofemailsaddress]'
    def handle(self, *args, **options):
        if not args:
            import sys
            emails = sys.stdin.read()
        else:
            _all = []
            for arg in args:
                _all.append(open(arg).read())
            emails = '\n'.join(_all)

        if not emails.strip():
            raise CommandError("No email addresses supplied")

        emails = [x.strip() for x in emails.splitlines()
                  if x.strip() and not x.startswith('#')]
        # removes dupes
        emails = set(emails)
        for email in emails:
            self.import_user(email)

    def import_user(self, email):
        try:
            user = User.objects.get(email__iexact=email)
            if user.first_name:
                print "Already have:", email
                print "\t", user.date_joined
                return
        except User.DoesNotExist:
            user = None

        # now user is either None or something that needs to be filled
        if not user:
            user = User(email=email)

        details = fetch_user_details(email, force_refresh=True)
        if not details:
            print "Can't find", email, "in LDAP :("
            return
        user.first_name = details['givenName']
        user.last_name = details['sn']
        user.username = details['uid']
        user.set_unusable_password()

        print "Created", email
        #print "\t", get_user_name(user)
