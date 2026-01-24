from django.core.management.base import BaseCommand
from voting.models import Vote, Candidate, Constituency, VoterProfile
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Creates test voting data'

    def handle(self, *args, **kwargs):
        # Make sure you have a constituency
        const, _ = Constituency.objects.get_or_create(
            name="Test District",
            defaults={'registered_voters': 100}
        )
        
        # Create candidates
        candidate1, _ = Candidate.objects.get_or_create(
            name="Candidate A",
            party="Party Alpha",
            constituency=const
        )
        candidate2, _ = Candidate.objects.get_or_create(
            name="Candidate B",
            party="Party Beta",
            constituency=const
        )
        
        candidates = [candidate1, candidate2]
        
        # Create 30 test votes
        for i in range(30):
            # Create user
            username = f"testvoter{i}"
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@test.com",
                    password="test123"
                )
                
                # Create voter profile
                VoterProfile.objects.create(
                    user=user,
                    voter_id=f"V{2000+i}",
                    constituency=const,
                    age_group="18-25"
                )
            
            # Check if vote exists
            if not Vote.objects.filter(user=user).exists():
                # Determine voting hour
                if i < 20:
                    hour = random.randint(9, 18)  # Normal hours
                else:
                    hour = random.randint(2, 5)   # Anomaly hours
                
                # Create timestamp
                timestamp = datetime.now() - timedelta(days=random.randint(0, 7))
                timestamp = timestamp.replace(hour=hour, minute=random.randint(0, 59))
                
                # Create vote
                vote = Vote.objects.create(
                    user=user,
                    candidate=random.choice(candidates),
                    vote_hour=hour,
                    vote_day=timestamp.strftime('%A')
                )
                # Update timestamp
                Vote.objects.filter(id=vote.id).update(timestamp=timestamp)
                
                self.stdout.write(f"Created vote for {username} at {hour}:00")
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Created test votes! Total: {Vote.objects.count()}')
        )