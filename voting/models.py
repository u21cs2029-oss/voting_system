"""
Enhanced models.py with analytics support
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Constituency(models.Model):
    """Model for electoral constituencies"""
    name = models.CharField(max_length=100, unique=True)
    registered_voters = models.IntegerField(default=0, help_text="Total registered voters")
    
    class Meta:
        verbose_name_plural = "Constituencies"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_turnout_percentage(self):
        """Calculate voter turnout percentage"""
        total_votes = Vote.objects.filter(candidate__constituency=self).count()
        if self.registered_voters > 0:
            return round((total_votes / self.registered_voters) * 100, 2)
        return 0


class VoterProfile(models.Model):
    """Model for voter information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    voter_id = models.CharField(max_length=20, unique=True)
    constituency = models.ForeignKey(Constituency, on_delete=models.CASCADE)
    age_group = models.CharField(
        max_length=20,
        choices=[
            ('18-25', '18-25'),
            ('26-35', '26-35'),
            ('36-50', '36-50'),
            ('51-65', '51-65'),
            ('65+', '65+'),
        ],
        null=True,
        blank=True,
        help_text="Age group for demographic analysis"
    )
    
    class Meta:
        ordering = ['voter_id']
    
    def __str__(self):
        return f"{self.voter_id} - {self.user.username}"


class Candidate(models.Model):
    """Model for election candidates"""
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    constituency = models.ForeignKey(Constituency, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='candidate_photos/', blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'constituency']
    
    def __str__(self):
        return f"{self.name} ({self.party}) - {self.constituency.name}"
    
    def get_vote_count(self):
        """Get total votes for this candidate"""
        return Vote.objects.filter(candidate=self).count()
    
    def get_vote_percentage(self):
        """Get percentage of votes in constituency"""
        total_votes = Vote.objects.filter(candidate__constituency=self.constituency).count()
        my_votes = self.get_vote_count()
        if total_votes > 0:
            return round((my_votes / total_votes) * 100, 2)
        return 0


class Vote(models.Model):
    """Model for votes cast - Enhanced with analytics fields"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Analytics fields
    vote_hour = models.IntegerField(null=True, blank=True, help_text="Hour of day (0-23)")
    vote_day = models.CharField(max_length=10, null=True, blank=True, help_text="Day of week")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'candidate']
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['vote_hour']),
        ]
    
    def __str__(self):
        return f"Vote by {self.user.username} for {self.candidate.name}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-populate analytics fields"""
        if not self.vote_hour:
            self.vote_hour = self.timestamp.hour if self.timestamp else timezone.now().hour
        if not self.vote_day:
            self.vote_day = self.timestamp.strftime('%A') if self.timestamp else timezone.now().strftime('%A')
        super().save(*args, **kwargs)


class OTP(models.Model):
    """OTP model for verification"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.username}"
    
    def is_expired(self, expiry_minutes=10):
        """Check if OTP has expired"""
        from datetime import timedelta
        expiry_time = self.created_at + timedelta(minutes=expiry_minutes)
        return timezone.now() > expiry_time


class VotingAnalytics(models.Model):
    """Store analytics snapshots for ML training"""
    constituency = models.ForeignKey(Constituency, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total_votes = models.IntegerField(default=0)
    turnout_percentage = models.FloatField(default=0.0)
    votes_per_hour_avg = models.FloatField(default=0.0)
    peak_voting_hour = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['constituency', 'date']
    
    def __str__(self):
        return f"Analytics for {self.constituency.name} on {self.date}"