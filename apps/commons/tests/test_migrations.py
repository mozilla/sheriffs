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

import re
from os import listdir
from os.path import join, dirname

import test_utils

import manage


class MigrationTests(test_utils.TestCase):
    """Sanity checks for the SQL migration scripts."""

    @staticmethod
    def _migrations_path():
        """Return the absolute path to the migration script folder."""
        return manage.path('migrations')

    def test_unique(self):
        """Assert that the numeric prefixes of the DB migrations are unique."""
        leading_digits = re.compile(r'^\d+')
        seen_numbers = set()
        path = self._migrations_path()
        for filename in listdir(path):
            match = leading_digits.match(filename)
            if match:
                number = match.group()
                if number in seen_numbers:
                    self.fail('There is more than one migration #%s in %s.' %
                              (number, path))
                seen_numbers.add(number)

    def test_innodb_and_utf8(self):
        """Make sure each created table uses the InnoDB engine and UTF-8."""
        # Heuristic: make sure there are at least as many "ENGINE=InnoDB"s as
        # "CREATE TABLE"s. (There might be additional "InnoDB"s in ALTER TABLE
        # statements, which are fine.)
        path = self._migrations_path()
        for filename in sorted(listdir(path)):
            with open(join(path, filename)) as f:
                contents = f.read()
            creates = contents.count('CREATE TABLE')
            engines = contents.count('ENGINE=InnoDB')
            encodings = (contents.count('CHARSET=utf8') +
                         contents.count('CHARACTER SET utf8'))
            assert engines >= creates, ("There weren't as many "
                'occurrences of "ENGINE=InnoDB" as of "CREATE TABLE" in '
                'migration %s.' % filename)
            assert encodings >= creates, ("There weren't as many "
                'UTF-8 declarations as "CREATE TABLE" occurrences in '
                'migration %s.' % filename)
