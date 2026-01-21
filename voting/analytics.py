"""
Data Science Analytics Module for Voting System

This module implements:
1. Voting Pattern Analysis
2. Voter Turnout Prediction (ML)
3. Anomaly Detection
4. Statistical Analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg
import warnings
warnings.filterwarnings('ignore')

# Machine Learning
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

# Anomaly Detection
from scipy import stats
from sklearn.ensemble import IsolationForest

# Visualization (for saving plots)
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns


class VotingPatternAnalyzer:
    """
    Analyzes voting patterns to identify trends and insights
    """
    
    def __init__(self, votes_queryset):
        """
        Initialize with votes queryset
        
        Args:
            votes_queryset: Django queryset of Vote objects
        """
        self.votes = votes_queryset
        self.df = None
        
    def prepare_data(self):
        """
        Convert Django queryset to Pandas DataFrame
        
        Returns:
            pd.DataFrame: Votes data with analytics columns
        """
        # Extract vote data
        data = []
        for vote in self.votes:
            data.append({
                'timestamp': vote.timestamp,
                'hour': vote.vote_hour,
                'day': vote.vote_day,
                'candidate': vote.candidate.name,
                'party': vote.candidate.party,
                'constituency': vote.candidate.constituency.name,
                'user_id': vote.user.id
            })
        
        self.df = pd.DataFrame(data)
        
        # Add derived columns
        if not self.df.empty:
            self.df['date'] = pd.to_datetime(self.df['timestamp']).dt.date
            self.df['time_of_day'] = pd.cut(
                self.df['hour'],
                bins=[0, 6, 12, 18, 24],
                labels=['Night', 'Morning', 'Afternoon', 'Evening']
            )
        
        return self.df
    
    def get_hourly_distribution(self):
        """
        Analyze voting distribution by hour
        
        Returns:
            dict: Hour-wise vote counts
        """
        if self.df is None:
            self.prepare_data()
        
        if self.df.empty:
            return {}
        
        hourly = self.df.groupby('hour').size().to_dict()
        return hourly
    
    def get_peak_voting_times(self):
        """
        Identify peak voting hours
        
        Returns:
            dict: Peak hour information
        """
        hourly = self.get_hourly_distribution()
        
        if not hourly:
            return {'peak_hour': None, 'peak_votes': 0}
        
        peak_hour = max(hourly, key=hourly.get)
        
        return {
            'peak_hour': peak_hour,
            'peak_votes': hourly[peak_hour],
            'hourly_distribution': hourly
        }
    
    def get_constituency_wise_turnout(self):
        """
        Calculate turnout percentage by constituency
        
        Returns:
            dict: Constituency-wise statistics
        """
        if self.df is None:
            self.prepare_data()
        
        if self.df.empty:
            return {}
        
        const_stats = self.df.groupby('constituency').agg({
            'user_id': 'count'
        }).rename(columns={'user_id': 'votes'}).to_dict()
        
        return const_stats['votes']
    
    def get_party_performance(self):
        """
        Analyze party-wise performance
        
        Returns:
            dict: Party-wise vote counts and percentages
        """
        if self.df is None:
            self.prepare_data()
        
        if self.df.empty:
            return {}
        
        party_stats = self.df.groupby('party').size()
        total_votes = len(self.df)
        
        result = {}
        for party, votes in party_stats.items():
            result[party] = {
                'votes': int(votes),
                'percentage': round((votes / total_votes) * 100, 2)
            }
        
        return result


class TurnoutPredictor:
    """
    Machine Learning model to predict voter turnout
    
    Uses historical data to predict future turnout based on:
    - Time of day
    - Day of week
    - Constituency demographics
    """
    
    def __init__(self):
        self.model = LogisticRegression(max_iter=1000)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, df):
        """
        Prepare features for ML model
        
        Args:
            df: DataFrame with voting data
            
        Returns:
            np.array: Feature matrix
        """
        # One-hot encode categorical variables
        features = pd.get_dummies(df[['hour', 'day']], drop_first=True)
        return features.values
    
    def train(self, votes_data):
        """
        Train the turnout prediction model
        
        Args:
            votes_data: Historical voting data
            
        Returns:
            dict: Training metrics
        """
        if len(votes_data) < 10:
            return {
                'success': False,
                'message': 'Insufficient data for training (need at least 10 votes)'
            }
        
        # Prepare data
        df = pd.DataFrame(votes_data)
        
        # Create target: 1 if vote cast, 0 otherwise (for demonstration)
        # In real scenario, you'd have registered voters who didn't vote
        df['voted'] = 1
        
        # Prepare features
        X = self.prepare_features(df)
        y = df['voted'].values
        
        # Split data
        if len(X) < 10:
            # Not enough data to split, use all for training
            X_train, X_test = X, X
            y_train, y_test = y, y
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        return {
            'success': True,
            'train_accuracy': round(train_score * 100, 2),
            'test_accuracy': round(test_score * 100, 2),
            'samples_trained': len(X_train)
        }
    
    def predict_turnout_probability(self, hour, day):
        """
        Predict probability of turnout for given time
        
        Args:
            hour: Hour of day (0-23)
            day: Day of week
            
        Returns:
            float: Probability (0-1)
        """
        if not self.is_trained:
            return 0.5  # Default probability
        
        # Create sample data
        sample = pd.DataFrame([{'hour': hour, 'day': day}])
        features = self.prepare_features(sample)
        features_scaled = self.scaler.transform(features)
        
        probability = self.model.predict_proba(features_scaled)[0][1]
        return round(probability, 3)


class AnomalyDetector:
    """
    Detect suspicious voting patterns using statistical methods
    
    Methods:
    1. Z-Score for outlier detection
    2. Isolation Forest for anomaly detection
    """
    
    def __init__(self, votes_queryset):
        self.votes = votes_queryset
        self.df = None
        
    def prepare_data(self):
        """Prepare data for anomaly detection"""
        data = []
        for vote in self.votes:
            data.append({
                'user_id': vote.user.id,
                'timestamp': vote.timestamp,
                'hour': vote.vote_hour,
                'constituency': vote.candidate.constituency.name,
            })
        
        self.df = pd.DataFrame(data)
        return self.df
    
    def detect_unusual_voting_times(self, z_threshold=2):
        """
        Detect votes cast at unusual hours using Z-score
        
        Args:
            z_threshold: Z-score threshold for outliers
            
        Returns:
            list: Suspicious voting times
        """
        if self.df is None:
            self.prepare_data()
        
        if self.df.empty or len(self.df) < 3:
            return []
        
        # Calculate Z-scores for voting hours
        hourly_counts = self.df.groupby('hour').size()
        
        if len(hourly_counts) < 2:
            return []
        
        z_scores = np.abs(stats.zscore(hourly_counts))
        
        # Find anomalies
        anomalies = []
        for hour, z_score in zip(hourly_counts.index, z_scores):
            if z_score > z_threshold:
                anomalies.append({
                    'hour': int(hour),
                    'votes': int(hourly_counts[hour]),
                    'z_score': round(float(z_score), 2),
                    'status': 'Unusual high activity'
                })
        
        return anomalies
    
    def detect_duplicate_patterns(self):
        """
        Detect potential duplicate voting patterns
        
        Returns:
            list: Suspicious patterns
        """
        if self.df is None:
            self.prepare_data()
        
        if self.df.empty:
            return []
        
        # Check for multiple votes from same user (shouldn't happen)
        duplicate_voters = self.df.groupby('user_id').size()
        duplicates = duplicate_voters[duplicate_voters > 1]
        
        suspicious = []
        for user_id, count in duplicates.items():
            suspicious.append({
                'user_id': int(user_id),
                'vote_count': int(count),
                'issue': 'Multiple votes detected'
            })
        
        return suspicious
    
    def get_anomaly_report(self):
        """
        Generate comprehensive anomaly detection report
        
        Returns:
            dict: Complete anomaly analysis
        """
        unusual_times = self.detect_unusual_voting_times()
        duplicates = self.detect_duplicate_patterns()
        
        return {
            'unusual_voting_times': unusual_times,
            'duplicate_patterns': duplicates,
            'total_anomalies': len(unusual_times) + len(duplicates),
            'status': 'Clean' if (len(unusual_times) + len(duplicates)) == 0 else 'Anomalies Detected'
        }


def generate_voting_insights(votes_queryset):
    """
    Generate comprehensive insights from voting data
    
    Args:
        votes_queryset: Django queryset of votes
        
    Returns:
        dict: Complete analytics report
    """
    # Pattern Analysis
    pattern_analyzer = VotingPatternAnalyzer(votes_queryset)
    pattern_analyzer.prepare_data()
    
    # Anomaly Detection
    anomaly_detector = AnomalyDetector(votes_queryset)
    
    # Generate insights
    insights = {
        'total_votes': votes_queryset.count(),
        'peak_times': pattern_analyzer.get_peak_voting_times(),
        'hourly_distribution': pattern_analyzer.get_hourly_distribution(),
        'constituency_turnout': pattern_analyzer.get_constituency_wise_turnout(),
        'party_performance': pattern_analyzer.get_party_performance(),
        'anomalies': anomaly_detector.get_anomaly_report(),
    }
    
    return insights