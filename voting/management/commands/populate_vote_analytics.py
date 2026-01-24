from django.core.management.base import BaseCommand
from voting.models import Vote
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populate vote_hour and vote_day for existing votes'

    def handle(self, *args, **kwargs):
        votes = Vote.objects.all()
        updated = 0
        
        for vote in votes:
            if vote.vote_hour is None:
                vote.vote_hour = vote.timestamp.hour
            if vote.vote_day is None:
                vote.vote_day = vote.timestamp.strftime('%A')
            vote.save()
            updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Updated {updated} votes with analytics data')
        )