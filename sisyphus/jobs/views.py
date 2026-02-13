from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

if TYPE_CHECKING:
    import uuid as uuid_mod

    from django.http import HttpRequest, HttpResponse

    from sisyphus.core.types import HtmxHttpRequest

from sisyphus.accounts.models import UserProfile
from sisyphus.jobs.models import Job, JobNote

SORT_OPTIONS = {
    'title': 'title',
    '-title': '-title',
    'company': 'company__name',
    '-company': '-company__name',
    'location': 'location__name',
    '-location': '-location__name',
    'date_posted': 'date_posted',
    '-date_posted': '-date_posted',
    'status': 'status',
    '-status': '-status',
}


@login_required
def job_list(request: HttpRequest) -> HttpResponse:
    """Display paginated list of jobs with filtering and sorting."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    jobs = Job.objects.filter(user=profile).select_related('company', 'location')

    search = request.GET.get('q', '').strip()
    if search:
        jobs = jobs.filter(Q(title__icontains=search) | Q(company__name__icontains=search))

    status = request.GET.get('status')
    if status:
        jobs = jobs.filter(status=status)

    flexibility = request.GET.get('flexibility')
    if flexibility:
        jobs = jobs.filter(flexibility=flexibility)

    sort = request.GET.get('sort', '-date_posted')
    if sort in SORT_OPTIONS:
        jobs = jobs.order_by(SORT_OPTIONS[sort])
    else:
        sort = '-date_posted'
        jobs = jobs.order_by('-date_posted')

    paginator = Paginator(jobs, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'jobs/job_list.html',
        {
            'page': page,
            'status_choices': Job.Status.choices,
            'flexibility_choices': Job.Flexibility.choices,
            'current_search': search,
            'current_status': status,
            'current_flexibility': flexibility,
            'current_sort': sort,
        },
    )


@login_required
def job_detail(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Display job detail page."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job.objects.select_related('company', 'location'), uuid=uuid, user=profile)
    return render(
        request,
        'jobs/job_detail.html',
        {
            'job': job,
            'notes': job.notes.all(),
            'events': job.events.order_by('-created_at'),
            'status_choices': Job.Status.choices,
        },
    )


@login_required
def job_update_status(request: HtmxHttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Update a job's status."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, uuid=uuid, user=profile)
    new_status = request.POST.get('status')

    if new_status in Job.Status.values:
        job.update_status(new_status)
        job.refresh_from_db()

    if request.htmx:
        return render(
            request,
            'jobs/job_status_with_history.html',
            {
                'job': job,
                'events': job.events.order_by('-created_at'),
                'status_choices': Job.Status.choices,
            },
        )

    return redirect('jobs:job_detail', uuid=uuid)


@login_required
def job_add_note(request: HtmxHttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Add a note to a job."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, uuid=uuid, user=profile)
    text = request.POST.get('text', '').strip()

    if text:
        job.add_note(text)

    if request.htmx:
        return render(request, 'jobs/job_notes_inner.html', {'job': job, 'notes': job.notes.all()})

    return redirect('jobs:job_detail', uuid=uuid)


@login_required
def job_delete_note(request: HtmxHttpRequest, uuid: uuid_mod.UUID, note_id: int) -> HttpResponse:
    """Delete a note from a job."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    note = get_object_or_404(JobNote, id=note_id, job__uuid=uuid, job__user=profile)
    job = note.job
    note.delete()

    if request.htmx:
        return render(request, 'jobs/job_notes_inner.html', {'job': job, 'notes': job.notes.all()})

    return redirect('jobs:job_detail', uuid=uuid)


@login_required
def job_review(request: HttpRequest) -> HttpResponse:
    """Display the job review page for triaging jobs."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    filter_status = request.GET.get('status', 'new')
    if filter_status not in ['new', 'saved']:
        filter_status = 'new'

    job = (
        Job.objects.filter(status=filter_status, populated=True, user=profile)
        .select_related('company', 'location', 'search_run__search')
        .order_by('-date_posted')
        .first()
    )

    new_count = Job.objects.filter(status=Job.Status.NEW, populated=True, user=profile).count()
    saved_count = Job.objects.filter(status=Job.Status.SAVED, populated=True, user=profile).count()

    return render(
        request,
        'jobs/job_review.html',
        {
            'job': job,
            'new_count': new_count,
            'saved_count': saved_count,
            'current_filter': filter_status,
        },
    )


@login_required
def job_review_action(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Process a review action on a job."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(Job, uuid=uuid, user=profile)
    new_status = request.POST.get('status')

    if new_status in Job.Status.values:
        job.update_status(new_status)

    filter_status = request.GET.get('filter', 'new')
    return redirect(f'{reverse("jobs:job_review")}?status={filter_status}')
