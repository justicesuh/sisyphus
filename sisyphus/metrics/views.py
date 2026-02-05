import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Min
from django.db.models.functions import TruncDay, TruncWeek
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

RESPONSE_STATUSES = {
    Job.Status.INTERVIEWING,
    Job.Status.OFFER,
    Job.Status.REJECTED,
    Job.Status.GHOSTED,
    Job.Status.ACCEPTED,
    Job.Status.WITHDRAWN,
}


@login_required
def index(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # --- Existing: Status counts & applied cards ---
    status_counts = dict(
        Job.objects.values_list('status').annotate(count=Count('id')).order_by()
    )

    to_review = Job.objects.filter(status=Job.Status.NEW, populated=True).count()

    applied_events = JobEvent.objects.filter(new_status=Job.Status.APPLIED)
    applied_today = applied_events.filter(created_at__gte=today_start).count()
    applied_7d = applied_events.filter(
        created_at__gte=now - timedelta(days=7)
    ).count()
    applied_30d = applied_events.filter(
        created_at__gte=now - timedelta(days=30)
    ).count()
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

    # --- Reusable: applied job IDs ---
    applied_job_ids = list(
        applied_events.values_list('job_id', flat=True).distinct()
    )

    # === 1. Application Pipeline ===
    responded_count = (
        JobEvent.objects.filter(job_id__in=applied_job_ids, new_status__in=RESPONSE_STATUSES)
        .values('job_id')
        .distinct()
        .count()
    )
    response_rate = (
        round(responded_count / len(applied_job_ids) * 100)
        if applied_job_ids
        else 0
    )

    active_pipeline = Job.objects.filter(
        status__in=[Job.Status.INTERVIEWING, Job.Status.OFFER]
    ).count()

    offer_job_count = (
        JobEvent.objects.filter(
            job_id__in=applied_job_ids,
            new_status__in=[Job.Status.OFFER, Job.Status.ACCEPTED],
        )
        .values('job_id')
        .distinct()
        .count()
    )
    offer_rate = (
        round(offer_job_count / len(applied_job_ids) * 100)
        if applied_job_ids
        else 0
    )

    # === 2. Job Discovery ===
    seven_days_ago = now - timedelta(days=7)
    daily_found = (
        Job.objects.filter(date_found__gte=seven_days_ago)
        .annotate(day=TruncDay('date_found'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    daily_found_chart = {
        'labels': [],
        'counts': [],
    }
    for entry in daily_found:
        daily_found_chart['labels'].append(entry['day'].strftime('%a %m/%d'))
        daily_found_chart['counts'].append(entry['count'])

    dismiss_events = JobEvent.objects.filter(
        old_status=Job.Status.NEW, new_status=Job.Status.DISMISSED
    ).count()
    save_events = JobEvent.objects.filter(
        old_status=Job.Status.NEW, new_status=Job.Status.SAVED
    ).count()
    dismiss_rate_total = dismiss_events + save_events
    dismiss_rate = (
        round(dismiss_events / dismiss_rate_total * 100)
        if dismiss_rate_total
        else 0
    )

    pending_populated = Job.objects.filter(
        status=Job.Status.NEW, populated=True
    ).count()
    pending_unpopulated = Job.objects.filter(
        status=Job.Status.NEW, populated=False
    ).count()
    pending_review_chart = {
        'labels': ['Populated', 'Unpopulated'],
        'counts': [pending_populated, pending_unpopulated],
        'colors': ['#198754', '#ffc107'],
    }

    # === 3. Time-based Trends ===
    twelve_weeks_ago = now - timedelta(weeks=12)
    weekly_apps = (
        JobEvent.objects.filter(
            new_status=Job.Status.APPLIED, created_at__gte=twelve_weeks_ago
        )
        .annotate(week=TruncWeek('created_at'))
        .values('week')
        .annotate(count=Count('id'))
        .order_by('week')
    )
    weekly_apps_chart = {
        'labels': [],
        'counts': [],
    }
    for entry in weekly_apps:
        weekly_apps_chart['labels'].append(entry['week'].strftime('%m/%d'))
        weekly_apps_chart['counts'].append(entry['count'])

    # Avg saved→applied (days)
    saved_dates = dict(
        JobEvent.objects.filter(
            job_id__in=applied_job_ids, new_status=Job.Status.SAVED
        )
        .values('job_id')
        .annotate(earliest=Min('created_at'))
        .values_list('job_id', 'earliest')
    )
    applied_dates = dict(
        JobEvent.objects.filter(
            job_id__in=applied_job_ids, new_status=Job.Status.APPLIED
        )
        .values('job_id')
        .annotate(earliest=Min('created_at'))
        .values_list('job_id', 'earliest')
    )
    saved_to_applied_deltas = []
    for job_id in applied_job_ids:
        s = saved_dates.get(job_id)
        a = applied_dates.get(job_id)
        if s and a and a > s:
            saved_to_applied_deltas.append((a - s).total_seconds() / 86400)
    avg_saved_to_applied = (
        round(sum(saved_to_applied_deltas) / len(saved_to_applied_deltas), 1)
        if saved_to_applied_deltas
        else None
    )

    # Avg applied→response (days)
    response_dates = dict(
        JobEvent.objects.filter(
            job_id__in=applied_job_ids, new_status__in=RESPONSE_STATUSES
        )
        .values('job_id')
        .annotate(earliest=Min('created_at'))
        .values_list('job_id', 'earliest')
    )
    applied_to_response_deltas = []
    for job_id in applied_job_ids:
        a = applied_dates.get(job_id)
        r = response_dates.get(job_id)
        if a and r and r > a:
            applied_to_response_deltas.append((r - a).total_seconds() / 86400)
    avg_applied_to_response = (
        round(
            sum(applied_to_response_deltas) / len(applied_to_response_deltas),
            1,
        )
        if applied_to_response_deltas
        else None
    )

    return render(
        request,
        'index.html',
        {
            # Existing
            'to_review': to_review,
            'applied_today': applied_today,
            'applied_7d': applied_7d,
            'applied_30d': applied_30d,
            'applied_total': applied_total,
            'status_chart_json': json.dumps(status_chart),
            # 1. Application Pipeline
            'response_rate': response_rate,
            'active_pipeline': active_pipeline,
            'offer_rate': offer_rate,
            # 2. Job Discovery
            'daily_found_chart_json': json.dumps(daily_found_chart),
            'dismiss_rate': dismiss_rate,
            'save_events': save_events,
            'dismiss_events': dismiss_events,
            'pending_review_chart_json': json.dumps(pending_review_chart),
            # 3. Time-based Trends
            'weekly_apps_chart_json': json.dumps(weekly_apps_chart),
            'avg_saved_to_applied': avg_saved_to_applied,
            'avg_applied_to_response': avg_applied_to_response,
        },
    )
