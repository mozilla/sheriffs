from django.db import models
from django.contrib.auth.models import User

def get_user_profile(user):
    try:
        return user.get_profile()
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(user=user)

class UserProfile(models.Model):
    user = models.ForeignKey(User)
    notes = models.TextField(blank=True)
