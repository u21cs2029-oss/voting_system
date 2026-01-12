from django.db import models
from django.contrib.auth.models import User
class Constituency(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    total_seats = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

class Candidate(models.Model):
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    constituency = models.ForeignKey(
        Constituency,
        on_delete=models.CASCADE
    )
    photo = models.ImageField(
        upload_to='candidate_photos/',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.party})"


    def __str__(self):
        return f"{self.name} ({self.party})"


class Vote(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
class VoterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    voter_id = models.CharField(max_length=50, unique=True)
    constituency = models.ForeignKey(
        Constituency,
        on_delete=models.SET_NULL,
        null=True
    )


class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username}"
