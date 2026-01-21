"""
Analytics Dashboard Views

These views create the admin analytics dashboard
with Data Science insights
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
import json

from .models import Vote, Candidate, Constituency, VoterProfile
from .analytics import (
    VotingPatternAnalyzer,
    TurnoutPredictor,
    AnomalyDetector,
    generate_voting_insights
)


@staff_member_required
def analytics_dashboard(request):
    """
    Main analytics dashboard view
    
    Shows:
    - Overall statistics
    - Voting patterns
    - ML predictions
    - Anomaly detection results
    """
    # Get all votes
    all_votes = Vote.objects.all().select_related('candidate', 'user')
    
    # Overall Statistics
    total_votes = all_votes.count()
    total_voters = VoterProfile.objects.count()
    total_constituencies = Constituency.objects.count()
    turnout_percentage = (total_votes / total_voters * 100) if total_voters > 0 else 0
    
    # Generate comprehensive insights
    if total_votes > 0:
        insights = generate_voting_insights(all_votes)
    else:
        insights = {
            'total_votes': 0,
            'peak_times': {},
            'hourly_distribution': {},
            'constituency_turnout': {},
            'party_performance': {},
            'anomalies': {'total_anomalies': 0, 'status': 'No Data'}
        }
    
    # Prepare data for charts
    hourly_data = insights.get('hourly_distribution', {})
    hourly_labels = list(hourly_data.keys())
    hourly_values = list(hourly_data.values())
    
    # Party performance data
    party_data = insights.get('party_performance', {})
    party_labels = list(party_data.keys())
    party_values = [data['votes'] for data in party_data.values()]
    
    context = {
        # Overall Stats
        'total_votes': total_votes,
        'total_voters': total_voters,
        'total_constituencies': total_constituencies,
        'turnout_percentage': round(turnout_percentage, 2),
        
        # Insights
        'insights': insights,
        
        # Chart Data (as JSON for JavaScript)
        'hourly_labels': json.dumps(hourly_labels),
        'hourly_values': json.dumps(hourly_values),
        'party_labels': json.dumps(party_labels),
        'party_values': json.dumps(party_values),
        
        # Anomalies
        'anomalies': insights.get('anomalies', {}),
        
        # Peak Times
        'peak_times': insights.get('peak_times', {}),
    }
    
    return render(request, 'voting/analytics_dashboard.html', context)


@staff_member_required
def pattern_analysis(request):
    """
    Detailed voting pattern analysis view
    
    Shows:
    - Time-based patterns
    - Constituency-wise analysis
    - Demographic insights
    """
    all_votes = Vote.objects.all().select_related('candidate', 'user')
    
    # Pattern Analysis
    analyzer = VotingPatternAnalyzer(all_votes)
    analyzer.prepare_data()
    
    # Get various patterns
    hourly_dist = analyzer.get_hourly_distribution()
    constituency_turnout = analyzer.get_constituency_wise_turnout()
    party_performance = analyzer.get_party_performance()
    peak_times = analyzer.get_peak_voting_times()
    
    # Day-wise distribution
    day_dist = {}
    if analyzer.df is not None and not analyzer.df.empty:
        day_dist = analyzer.df.groupby('day').size().to_dict()
    
    context = {
        'hourly_distribution': hourly_dist,
        'day_distribution': day_dist,
        'constituency_turnout': constituency_turnout,
        'party_performance': party_performance,
        'peak_times': peak_times,
        'total_votes': all_votes.count(),
    }
    
    return render(request, 'voting/pattern_analysis.html', context)


@staff_member_required
def ml_predictions(request):
    """
    Machine Learning predictions view
    
    Shows:
    - Turnout predictions
    - Model accuracy
    - Feature importance
    """
    all_votes = Vote.objects.all()
    
    # Prepare data for ML
    votes_data = []
    for vote in all_votes:
        votes_data.append({
            'hour': vote.vote_hour,
            'day': vote.vote_day,
            'constituency': vote.candidate.constituency.name,
        })
    
    # Train predictor
    predictor = TurnoutPredictor()
    training_results = predictor.train(votes_data)
    
    # Generate predictions for different times
    predictions = []
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    sample_hours = [9, 12, 15, 18, 21]  # Sample hours throughout the day
    
    if predictor.is_trained:
        for day in days[:3]:  # Show predictions for 3 days
            for hour in sample_hours:
                prob = predictor.predict_turnout_probability(hour, day)
                predictions.append({
                    'day': day,
                    'hour': f"{hour}:00",
                    'probability': prob,
                    'percentage': round(prob * 100, 1),
                    'status': 'High' if prob > 0.7 else 'Medium' if prob > 0.4 else 'Low'
                })
    
    context = {
        'training_results': training_results,
        'predictions': predictions,
        'total_training_samples': len(votes_data),
        'model_status': 'Trained' if predictor.is_trained else 'Insufficient Data',
    }
    
    return render(request, 'voting/ml_predictions.html', context)


@staff_member_required
def anomaly_detection(request):
    """
    Anomaly detection view
    
    Shows:
    - Unusual voting patterns
    - Suspicious activities
    - Integrity checks
    """
    all_votes = Vote.objects.all()
    
    # Detect anomalies
    detector = AnomalyDetector(all_votes)
    anomaly_report = detector.get_anomaly_report()
    
    # Additional checks
    # Check for votes outside normal hours (e.g., midnight voting)
    midnight_votes = all_votes.filter(vote_hour__in=[0, 1, 2, 3, 4, 5]).count()
    
    # Check for rapid voting (same minute)
    rapid_voting = []
    if all_votes.exists():
        # Group by minute and count
        from django.db.models.functions import TruncMinute
        minute_groups = all_votes.annotate(
            minute=TruncMinute('timestamp')
        ).values('minute').annotate(
            count=Count('id')
        ).filter(count__gt=10)  # More than 10 votes in same minute
        
        rapid_voting = list(minute_groups)
    
    context = {
        'anomaly_report': anomaly_report,
        'midnight_votes': midnight_votes,
        'rapid_voting_instances': len(rapid_voting),
        'rapid_voting_details': rapid_voting[:10],  # Show top 10
        'total_votes_analyzed': all_votes.count(),
        'integrity_score': calculate_integrity_score(anomaly_report, midnight_votes),
    }
    
    return render(request, 'voting/anomaly_detection.html', context)


def calculate_integrity_score(anomaly_report, midnight_votes):
    """
    Calculate overall integrity score (0-100)
    
    Higher score = better integrity
    """
    total_anomalies = anomaly_report.get('total_anomalies', 0)
    
    # Start with 100
    score = 100
    
    # Deduct points for anomalies
    score -= total_anomalies * 5  # 5 points per anomaly
    
    # Deduct points for midnight voting
    score -= midnight_votes * 2  # 2 points per midnight vote
    
    # Ensure score is between 0 and 100
    score = max(0, min(100, score))
    
    return round(score, 1)


@staff_member_required
def export_analytics_data(request):
    """
    Export analytics data as JSON
    
    Useful for further analysis or reporting
    """
    all_votes = Vote.objects.all()
    insights = generate_voting_insights(all_votes)
    
    from django.http import JsonResponse
    return JsonResponse(insights, safe=False)