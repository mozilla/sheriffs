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

import os
import shutil

from django.conf import settings
import test_utils

import manage


class AcceptedLocalesTest(test_utils.TestCase):
    """Test lazy evaluation of locale related settings.

    Verify that some localization-related settings are lazily evaluated based 
    on the current value of the DEV variable.  Depending on the value, 
    DEV_LANGUAGES or PROD_LANGUAGES should be used.

    """
    locale = manage.path('locale')
    locale_bkp = manage.path('locale_bkp')

    @classmethod
    def setup_class(cls):
        """Create a directory structure for locale/.

        Back up the existing locale/ directory and create the following 
        hierarchy in its place:

            - locale/en-US/LC_MESSAGES
            - locale/fr/LC_MESSAGES
            - locale/templates/LC_MESSAGES
            - locale/empty_file

        Also, set PROD_LANGUAGES to ('en-US',).

        """
        if os.path.exists(cls.locale_bkp):
            raise Exception('A backup of locale/ exists at %s which might '
                            'mean that previous tests didn\'t end cleanly. '
                            'Skipping the test suite.' % cls.locale_bkp)
        cls.DEV = settings.DEV
        cls.PROD_LANGUAGES = settings.PROD_LANGUAGES
        cls.DEV_LANGUAGES = settings.DEV_LANGUAGES
        settings.PROD_LANGUAGES = ('en-US',)
        os.rename(cls.locale, cls.locale_bkp)
        for loc in ('en-US', 'fr', 'templates'):
            os.makedirs(os.path.join(cls.locale, loc, 'LC_MESSAGES'))
        open(os.path.join(cls.locale, 'empty_file'), 'w').close()

    @classmethod
    def teardown_class(cls):
        """Remove the testing locale/ dir and bring back the backup."""

        settings.DEV = cls.DEV
        settings.PROD_LANGUAGES = cls.PROD_LANGUAGES
        settings.DEV_LANGUAGES = cls.DEV_LANGUAGES
        shutil.rmtree(cls.locale)
        os.rename(cls.locale_bkp, cls.locale)

    def test_build_dev_languages(self):
        """Test that the list of dev locales is built properly.

        On dev instances, the list of accepted locales should correspond to 
        the per-locale directories in locale/.

        """
        settings.DEV = True
        assert (settings.DEV_LANGUAGES == ['en-US', 'fr'] or
                settings.DEV_LANGUAGES == ['fr', 'en-US']), \
                'DEV_LANGUAGES do not correspond to the contents of locale/.'

    def test_dev_languages(self):
        """Test the accepted locales on dev instances.

        On dev instances, allow locales defined in DEV_LANGUAGES.

        """
        settings.DEV = True
        # simulate the successful result of the DEV_LANGUAGES list 
        # comprehension defined in settings.
        settings.DEV_LANGUAGES = ['en-US', 'fr']
        assert settings.LANGUAGE_URL_MAP == {'en-us': 'en-US', 'fr': 'fr'}, \
               ('DEV is True, but DEV_LANGUAGES are not used to define the '
                'allowed locales.')

    def test_prod_languages(self):
        """Test the accepted locales on prod instances.

        On stage/prod instances, allow locales defined in PROD_LANGUAGES.

        """
        settings.DEV = False
        assert settings.LANGUAGE_URL_MAP == {'en-us': 'en-US'}, \
               ('DEV is False, but PROD_LANGUAGES are not used to define the '
                'allowed locales.')
