import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.shortcuts import render
from django.utils import timezone

from sisyphus.jobs.models import Job, JobEvent


def _trend(current, previous):
    """Return dict with absolute percentage change and direction."""
    if previous == 0:
        if current > 0:
            return {'pct': '100%', 'direction': 'up'}
        return {'pct': '0%', 'direction': 'down'}
    pct = round((current - previous) / previous * 100)
    if pct > 0:
        return {'pct': f'{pct}%', 'direction': 'up'}
    return {'pct': f'{abs(pct)}%', 'direction': 'down'}


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
    user_tz = timezone.get_current_timezone()
    local_now = timezone.localtime(now, user_tz)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)

    # --- Existing: Status counts & applied cards ---
    status_counts = dict(Job.objects.values_list('status').annotate(count=Count('id')).order_by())

    to_review = Job.objects.filter(status=Job.Status.NEW, populated=True).count()

    applied_events = JobEvent.objects.filter(new_status=Job.Status.APPLIED)
    applied_today = applied_events.filter(created_at__gte=today_start).count()
    applied_7d = applied_events.filter(created_at__gte=now - timedelta(days=7)).count()
    applied_30d = applied_events.filter(created_at__gte=now - timedelta(days=30)).count()
    applied_total = applied_events.count()

    # Previous period counts for trend indicators
    yesterday_start = today_start - timedelta(days=1)
    prev_today = applied_events.filter(created_at__gte=yesterday_start, created_at__lt=today_start).count()
    prev_7d = applied_events.filter(
        created_at__gte=now - timedelta(days=14),
        created_at__lt=now - timedelta(days=7),
    ).count()
    prev_30d = applied_events.filter(
        created_at__gte=now - timedelta(days=60),
        created_at__lt=now - timedelta(days=30),
    ).count()

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
    applied_job_ids = list(applied_events.values_list('job_id', flat=True).distinct())

    # === 1. Application Pipeline ===
    responded_count = (
        JobEvent.objects.filter(job_id__in=applied_job_ids, new_status__in=RESPONSE_STATUSES)
        .values('job_id')
        .distinct()
        .count()
    )
    response_rate = round(responded_count / len(applied_job_ids) * 100) if applied_job_ids else 0

    active_pipeline = Job.objects.filter(status__in=[Job.Status.INTERVIEWING, Job.Status.OFFER]).count()

    offer_job_count = (
        JobEvent.objects.filter(
            job_id__in=applied_job_ids,
            new_status__in=[Job.Status.OFFER, Job.Status.ACCEPTED],
        )
        .values('job_id')
        .distinct()
        .count()
    )
    offer_rate = round(offer_job_count / len(applied_job_ids) * 100) if applied_job_ids else 0

    # === Activity Heatmap ===
    today = timezone.localdate()
    # Go back ~1 year, then extend to the most recent Sunday
    year_ago_raw = today - timedelta(days=364)
    # Roll back to the Sunday on or before that date
    start = year_ago_raw - timedelta(days=(year_ago_raw.weekday() + 1) % 7)
    daily_applied = {
        dt.date(): count
        for dt, count in applied_events.filter(created_at__date__gte=start)
        .annotate(day=TruncDay('created_at', tzinfo=user_tz))
        .values('day')
        .annotate(count=Count('id'))
        .values_list('day', 'count')
    }
    heatmap_weeks = []
    heatmap_months = []  # (week_index, month_label) for month headers
    current = start
    prev_month = None
    while current <= today:
        week = []
        for dow in range(7):
            day = current + timedelta(days=dow)
            if day > today:
                week.append(None)
            else:
                week.append(
                    {
                        'date': day.isoformat(),
                        'count': daily_applied.get(day, 0),
                    }
                )
                month_label = day.strftime('%b')
                if month_label != prev_month:
                    heatmap_months.append(
                        {
                            'week': len(heatmap_weeks),
                            'label': month_label,
                        }
                    )
                    prev_month = month_label
        heatmap_weeks.append(week)
        current += timedelta(days=7)

    max_applied = max(
        (cell['count'] for week in heatmap_weeks for cell in week if cell),
        default=1,
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
            'trend_today': _trend(applied_today, prev_today),
            'trend_7d': _trend(applied_7d, prev_7d),
            'trend_30d': _trend(applied_30d, prev_30d),
            'status_chart_json': json.dumps(status_chart),
            # 1. Application Pipeline
            'heatmap_json': json.dumps(
                {
                    'weeks': heatmap_weeks,
                    'months': heatmap_months,
                    'max': max_applied,
                }
            ),
            'response_rate': response_rate,
            'active_pipeline': active_pipeline,
            'offer_rate': offer_rate,
        },
    )
