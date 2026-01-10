from django.contrib import admin
from .models import Candidate, Vote, VoterProfile

admin.site.register(Candidate)
admin.site.register(Vote)
admin.site.register(VoterProfile)
