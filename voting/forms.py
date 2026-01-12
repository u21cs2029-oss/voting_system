from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Constituency


class VoterRegistrationForm(UserCreationForm):
    voter_id = forms.CharField(max_length=20, label="Voter ID")
    email = forms.EmailField(required=True)
    constituency = forms.ModelChoiceField(
        queryset=Constituency.objects.all(),
        empty_label="Select your Constituency"
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'voter_id',
            'constituency',
            'password1',
            'password2',
        )
