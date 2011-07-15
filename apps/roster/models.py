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

import datetime
from django.db import models
from uuidfield import UUIDField
from django.contrib.auth.models import User


class Slot(models.Model):

    user = models.ForeignKey(User)
    date = models.DateField(db_index=True)
    swap_needed = models.BooleanField(default=False)

    add_date = models.DateTimeField(default=datetime.datetime.now)
    modify_date = models.DateTimeField(default=datetime.datetime.now,
                                       auto_now=True)

    def __unicode__(self):
        return ("%s (%s)" %
                (self.user.username,
                 self.date.strftime('%d-%b-%Y')))

    def __repr__(self):  # pragma: no cover
        return ("<Slot: %r (%s)>" %
                (self.user.username,
                 self.date.strftime('%d-%b-%Y')))


class Swap(models.Model):

    slot = models.ForeignKey(Slot)
    user = models.ForeignKey(User, null=True)

    TYPE_OFFER = 'offer'
    TYPE_REQUEST = 'request'
    TYPE_CHOICES = (
      (TYPE_OFFER, 'Offer'),
      (TYPE_REQUEST, 'Request'),
    )
    type = models.CharField("Type", max_length=100,
                            choices=TYPE_CHOICES)

    STATE_UNANSWERED = 'unanswered'
    STATE_ACCEPTED = 'accepted'
    STATE_DECLINED = 'declined'
    STATE_CHOICES = (
      (STATE_UNANSWERED, "Unanswered"),
      (STATE_ACCEPTED, "Accepted"),
      (STATE_DECLINED, "Declined"),
    )
    state = models.CharField("State", max_length=100,
                             choices=STATE_CHOICES,
                             default=STATE_UNANSWERED)
    uuid = UUIDField(auto=True, db_index=True)
    comment = models.TextField("Comment", blank=True)

    add_date = models.DateTimeField(default=datetime.datetime.now)
    modify_date = models.DateTimeField(default=datetime.datetime.now)
