from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from sisyphus.companies.models import Company
from sisyphus.jobs.models import Job, JobNote


@login_required
def index(request):
    return render(request, 'index.html')


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

COMPANY_SORT_OPTIONS = {
    'name': 'name',
    '-name': '-name',
    'created_at': 'created_at',
    '-created_at': '-created_at',
    'job_count': 'job_count',
    '-job_count': '-job_count',
}


@login_required
def job_list(request):
    from django.db.models import Q

    jobs = Job.objects.select_related('company', 'location')

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

    return render(request, 'jobs/job_list.html', {
        'page': page,
        'status_choices': Job.Status.choices,
        'flexibility_choices': Job.Flexibility.choices,
        'current_search': search,
        'current_status': status,
        'current_flexibility': flexibility,
        'current_sort': sort,
    })


@login_required
def job_detail(request, uuid):
    job = get_object_or_404(Job.objects.select_related('company', 'location'), uuid=uuid)
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'notes': job.notes.all(),
        'events': job.events.all(),
        'status_choices': Job.Status.choices,
    })


@login_required
def job_update_status(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    job = get_object_or_404(Job, uuid=uuid)
    new_status = request.POST.get('status')

    if new_status in Job.Status.values:
        job.update_status(new_status)

    if request.htmx:
        return render(request, 'jobs/job_status_with_history.html', {
            'job': job,
            'events': job.events.all(),
            'status_choices': Job.Status.choices,
        })

    return redirect('web:job_detail', uuid=uuid)


@login_required
def job_add_note(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    job = get_object_or_404(Job, uuid=uuid)
    text = request.POST.get('text', '').strip()

    if text:
        job.add_note(text)

    if request.htmx:
        return render(request, 'jobs/job_notes_inner.html', {'job': job, 'notes': job.notes.all()})

    return redirect('web:job_detail', uuid=uuid)


@login_required
def job_delete_note(request, uuid, note_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    note = get_object_or_404(JobNote, id=note_id, job__uuid=uuid)
    job = note.job
    note.delete()

    if request.htmx:
        return render(request, 'jobs/job_notes_inner.html', {'job': job, 'notes': job.notes.all()})

    return redirect('web:job_detail', uuid=uuid)


@login_required
def company_list(request):
    from django.db.models import Count, Q

    companies = Company.objects.annotate(job_count=Count('jobs'))

    search = request.GET.get('q', '').strip()
    if search:
        companies = companies.filter(Q(name__icontains=search) | Q(website__icontains=search))

    banned = request.GET.get('banned')
    if banned == 'yes':
        companies = companies.filter(is_banned=True)
    elif banned == 'no':
        companies = companies.filter(is_banned=False)

    sort = request.GET.get('sort', 'name')
    if sort in COMPANY_SORT_OPTIONS:
        companies = companies.order_by(COMPANY_SORT_OPTIONS[sort])
    else:
        sort = 'name'
        companies = companies.order_by('name')

    paginator = Paginator(companies, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'companies/company_list.html', {
        'page': page,
        'current_search': search,
        'current_banned': banned,
        'current_sort': sort,
    })
