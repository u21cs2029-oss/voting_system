from django.db import models
from django.contrib.auth.models import User


class Candidate(models.Model):
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Vote(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
class VoterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    voter_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.voter_id}"
class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username}"
