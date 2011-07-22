# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
# 
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
# 
# The Original Code is Mozilla Sheriff Duty.
# 
# The Initial Developer of the Original Code is Mozilla Corporation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
# 
# Contributor(s):
# 
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
# 
# ***** END LICENSE BLOCK *****

from threading import local

from django.conf import settings
from django.core.urlresolvers import reverse as django_reverse
from django.utils.translation.trans_real import parse_accept_lang_header


# Thread-local storage for URL prefixes. Access with (get|set)_url_prefix.
_local = local()


def set_url_prefix(prefix):
    """Set the ``prefix`` for the current thread."""
    _local.prefix = prefix


def get_url_prefix():
    """Get the prefix for the current thread, or None."""
    return getattr(_local, 'prefix', None)


def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None):
    """Wraps Django's reverse to prepend the correct locale."""
    prefixer = get_url_prefix()

    if prefixer:
        prefix = prefix or '/'
    url = django_reverse(viewname, urlconf, args, kwargs, prefix)
    if prefixer:
        return prefixer.fix(url)
    else:
        return url


def find_supported(test):
    return [settings.LANGUAGE_URL_MAP[x] for
            x in settings.LANGUAGE_URL_MAP if
            x.split('-', 1)[0] == test.lower().split('-', 1)[0]]


class Prefixer(object):

    def __init__(self, request):
        self.request = request
        split = self.split_path(request.path_info)
        self.locale, self.shortened_path = split

    def split_path(self, path_):
        """
        Split the requested path into (locale, path).

        locale will be empty if it isn't found.
        """
        path = path_.lstrip('/')

        # Use partitition instead of split since it always returns 3 parts
        first, _, rest = path.partition('/')

        lang = first.lower()
        if lang in settings.LANGUAGE_URL_MAP:
            return settings.LANGUAGE_URL_MAP[lang], rest
        else:
            supported = find_supported(first)
            if len(supported):
                return supported[0], rest
            else:
                return '', path

    def get_language(self):
        """
        Return a locale code we support on the site using the
        user's Accept-Language header to determine which is best. This
        mostly follows the RFCs but read bug 439568 for details.
        """
        if 'lang' in self.request.GET:
            lang = self.request.GET['lang'].lower()
            if lang in settings.LANGUAGE_URL_MAP:
                return settings.LANGUAGE_URL_MAP[lang]

        if self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            best = self.get_best_language(
                self.request.META['HTTP_ACCEPT_LANGUAGE'])
            if best:
                return best
        return settings.LANGUAGE_CODE

    def get_best_language(self, accept_lang):
        """Given an Accept-Language header, return the best-matching language."""
        LUM = settings.LANGUAGE_URL_MAP
        PREFIXES = dict((x.split('-')[0], LUM[x]) for x in LUM)
        langs = dict(LUM)
        langs.update((k.split('-')[0], v) for k, v in LUM.items() if
                      k.split('-')[0] not in langs)
        ranked = parse_accept_lang_header(accept_lang)
        for lang, _ in ranked:
            lang = lang.lower()
            if lang in langs:
                return langs[lang]
            pre = lang.split('-')[0]
            if pre in langs:
                return langs[pre]
        # Could not find an acceptable language.
        return False

    def fix(self, path):
        path = path.lstrip('/')
        url_parts = [self.request.META['SCRIPT_NAME']]

        if path.partition('/')[0] not in settings.SUPPORTED_NONLOCALES:
            locale = self.locale if self.locale else self.get_language()
            url_parts.append(locale)

        url_parts.append(path)

        return '/'.join(url_parts)
