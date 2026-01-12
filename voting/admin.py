from django.contrib import admin
from .models import Constituency, Candidate, Vote, VoterProfile

admin.site.register(Constituency)
admin.site.register(Candidate)
admin.site.register(Vote)
admin.site.register(VoterProfile)
