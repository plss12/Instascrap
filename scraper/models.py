from django.db import models
from django.core.validators import URLValidator

class Insta(models.Model):
    profile = models.CharField(max_length=255)
    user = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    img = models.URLField()
    follower = models.BooleanField(default=False)
    following = models.BooleanField(default=False)

    class Meta:
        unique_together = ('profile', 'user')

class Profile(models.Model):
    profile = models.CharField(max_length=255, primary_key=True)
    img = models.URLField()
    followers = models.IntegerField()
    followings = models.IntegerField()