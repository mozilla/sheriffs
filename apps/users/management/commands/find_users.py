"""
Use this script to convert a list of email addresses to LDAP email addresses
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from .ldap_lookup import search_users

class Command(BaseCommand):  #pragma: no cover
    help = "Find users"
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
        verbosity = int(options['verbosity'])
        successes = []
        failures = []
        for email in emails:
            mail = self.import_user(email, verbose=verbosity > 1)
            if mail:
                successes.append((email, mail))
            else:
                failures.append(email)

        print "  WORKED  ".center(80, '=')
        for e, m in successes:
            print m.ljust(40),
            print "(was: %s)" % e
        print "  FAILED  ".center(80, '=')
        for e in failures:
            print e


    def import_user(self, email, verbose=False):
        if verbose:
            print email.ljust(40),
        try:
            user = User.objects.get(email__iexact=email)
            if user.first_name:
                if verbose:
                    print "Already have:"
                return user.email
        except User.DoesNotExist:
            pass

        results = search_users(email, 1,
           search_keys=('mail', 'bugzillaEmail'),
           force_refresh=False,
        )
        if results:
            if verbose: print "FOUND",
            if results[0]['mail'] != email:
                if verbose: print results[0]['mail']
            else:
                if verbose: print ""
            return results[0]['mail']
        else:
            if verbose: print ":("
