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
