import json

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from sisyphus.jobs.models import Job, JobEvent

STATUS_COLORS = {
    'new': '#0d6efd',
    'filtered': '#6c757d',
    'banned': '#dc3545',
    'saved': '#ffc107',
    'expired': '#343a40',
    'applied': '#198754',
    'dismissed': '#6c757d',
    'interviewing': '#0dcaf0',
    'offer': '#0dcaf0',
    'rejected': '#dc3545',
    'withdrawn': '#343a40',
    'ghosted': '#343a40',
    'accepted': '#198754',
}


@login_required
def index(request):
    status_counts = dict(
        Job.objects.values_list('status').annotate(count=Count('id')).order_by()
    )

    to_review = Job.objects.filter(status=Job.Status.NEW, populated=True).count()

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    applied_events = JobEvent.objects.filter(new_status=Job.Status.APPLIED)
    applied_today = applied_events.filter(created_at__gte=today_start).count()
    applied_7d = applied_events.filter(created_at__gte=now - timezone.timedelta(days=7)).count()
    applied_30d = applied_events.filter(created_at__gte=now - timezone.timedelta(days=30)).count()
    applied_total = applied_events.count()

    status_chart = {
        'labels': [],
        'values': [],
        'counts': [],
        'colors': [],
    }
    for value, label in Job.Status.choices:
        count = status_counts.get(value, 0)
        if count:
            status_chart['labels'].append(str(label))
            status_chart['values'].append(value)
            status_chart['counts'].append(count)
            status_chart['colors'].append(STATUS_COLORS.get(value, '#6c757d'))

    return render(request, 'index.html', {
        'to_review': to_review,
        'applied_today': applied_today,
        'applied_7d': applied_7d,
        'applied_30d': applied_30d,
        'applied_total': applied_total,
        'status_chart_json': json.dumps(status_chart),
    })
