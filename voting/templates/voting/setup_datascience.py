"""
Quick Setup Script for Data Science Features

Run this after installing libraries and updating models:
python setup_datascience.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voting_system.settings')
django.setup()

from voting.models import Vote, Constituency, VoterProfile
from django.utils import timezone

def update_existing_votes():
    """
    Update existing votes with analytics fields
    """
    print("\n" + "="*60)
    print("  Updating Existing Votes with Analytics Fields")
    print("="*60 + "\n")
    
    votes = Vote.objects.all()
    total = votes.count()
    
    if total == 0:
        print("No votes found. This is normal for a new system.")
        return
    
    print(f"Found {total} votes to update...")
    
    updated = 0
    for vote in votes:
        needs_update = False
        
        if not vote.vote_hour:
            vote.vote_hour = vote.timestamp.hour
            needs_update = True
        
        if not vote.vote_day:
            vote.vote_day = vote.timestamp.strftime('%A')
            needs_update = True
        
        if needs_update:
            vote.save()
            updated += 1
    
    print(f"✓ Updated {updated} votes with analytics fields")
    print(f"✓ {total - updated} votes already had analytics fields\n")


def setup_constituencies():
    """
    Ensure constituencies have registered voter counts
    """
    print("="*60)
    print("  Setting Up Constituency Data")
    print("="*60 + "\n")
    
    constituencies = Constituency.objects.all()
    
    for const in constituencies:
        # Count voters in this constituency
        voter_count = VoterProfile.objects.filter(constituency=const).count()
        
        if const.registered_voters == 0:
            const.registered_voters = voter_count
            const.save()
            print(f"✓ {const.name}: Set registered voters to {voter_count}")
        else:
            print(f"  {const.name}: Already configured ({const.registered_voters} voters)")
    
    print()


def create_sample_data():
    """
    Optionally create sample data for testing
    """
    print("="*60)
    print("  Sample Data Creation (Optional)")
    print("="*60 + "\n")
    
    response = input("Do you want to create sample votes for testing? (y/n): ")
    
    if response.lower() != 'y':
        print("Skipped sample data creation.\n")
        return
    
    # Import here to avoid errors if models aren't ready
    from voting.models import Candidate
    from django.contrib.auth.models import User
    import random
    from datetime import timedelta
    
    print("\nCreating sample data...")
    
    # Get or create test users
    candidates = list(Candidate.objects.all())
    if not candidates:
        print("❌ No candidates found. Please create candidates first via admin.")
        return
    
    # Create sample votes across different times
    hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    print("Creating 50 sample votes...")
    created = 0
    
    for i in range(50):
        try:
            # Create a sample user
            username = f"sample_user_{i}"
            
            # Check if user exists
            if User.objects.filter(username=username).exists():
                continue
            
            user = User.objects.create_user(
                username=username,
                email=f"{username}@test.com",
                password="test123"
            )
            
            # Random time
            hour = random.choice(hours)
            day = random.choice(days)
            
            # Random candidate
            candidate = random.choice(candidates)
            
            # Create voter profile
            VoterProfile.objects.create(
                user=user,
                voter_id=f"SAMPLE{i:04d}",
                constituency=candidate.constituency
            )
            
            # Create vote
            Vote.objects.create(
                user=user,
                candidate=candidate,
                vote_hour=hour,
                vote_day=day
            )
            
            created += 1
            
        except Exception as e:
            print(f"Warning: Could not create sample vote {i}: {e}")
            continue
    
    print(f"✓ Created {created} sample votes\n")


def verify_installation():
    """
    Verify all required libraries are installed
    """
    print("="*60)
    print("  Verifying Data Science Libraries")
    print("="*60 + "\n")
    
    required = {
        'pandas': 'Data manipulation',
        'numpy': 'Numerical computing',
        'sklearn': 'Machine learning',
        'matplotlib': 'Visualization',
        'seaborn': 'Statistical visualization',
        'scipy': 'Scientific computing'
    }
    
    all_installed = True
    
    for lib, description in required.items():
        try:
            __import__(lib)
            print(f"✓ {lib.ljust(15)} - {description}")
        except ImportError:
            print(f"✗ {lib.ljust(15)} - MISSING! Install with: pip install {lib}")
            all_installed = False
    
    print()
    
    if not all_installed:
        print("❌ Some libraries are missing. Please install them:")
        print("   pip install pandas numpy scikit-learn matplotlib seaborn scipy\n")
        return False
    else:
        print("✓ All Data Science libraries installed!\n")
        return True


def main():
    """
    Main setup function
    """
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  Data Science Feature Setup".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    print()
    
    # Step 1: Verify libraries
    if not verify_installation():
        print("Please install missing libraries and run again.")
        return
    
    # Step 2: Update existing votes
    update_existing_votes()
    
    # Step 3: Setup constituencies
    setup_constituencies()
    
    # Step 4: Optional sample data
    create_sample_data()
    
    # Final message
    print("="*60)
    print("  Setup Complete!")
    print("="*60)
    print()
    print("✓ All analytics fields updated")
    print("✓ Constituencies configured")
    print()
    print("Next steps:")
    print("1. Run server: python manage.py runserver")
    print("2. Login as admin: /admin/")
    print("3. Visit analytics: /analytics/")
    print()
    print("Analytics Dashboard URLs:")
    print("  • Main Dashboard:     /analytics/")
    print("  • Pattern Analysis:   /analytics/patterns/")
    print("  • ML Predictions:     /analytics/ml/")
    print("  • Anomaly Detection:  /analytics/anomalies/")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you've:")
        print("1. Installed all libraries")
        print("2. Run migrations: python manage.py migrate")
        print("3. Have votes in the database\n")