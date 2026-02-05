from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from sisyphus.jobs.models import Job


@login_required
def index(request):
    status_counts = dict(
        Job.objects.values_list('status').annotate(count=Count('id')).order_by()
    )

    to_review = Job.objects.filter(status=Job.Status.NEW, populated=True).count()

    return render(request, 'index.html', {
        'to_review': to_review,
        'saved': status_counts.get(Job.Status.SAVED, 0),
        'applied': status_counts.get(Job.Status.APPLIED, 0),
        'interviewing': status_counts.get(Job.Status.INTERVIEWING, 0),
    })
