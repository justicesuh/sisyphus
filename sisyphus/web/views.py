from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from sisyphus.jobs.models import Job


@login_required
def index(request):
    return render(request, 'index.html')


@login_required
def job_list(request):
    jobs = Job.objects.select_related('company', 'location').order_by('-date_posted')
    return render(request, 'jobs/job_list.html', {'jobs': jobs})
