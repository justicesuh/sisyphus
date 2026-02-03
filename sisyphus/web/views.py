from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from sisyphus.accounts.models import UserProfile, get_timezone_choices
from sisyphus.companies.models import Company
from sisyphus.jobs.models import Job, JobNote
from sisyphus.resumes.models import Resume


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
        'events': job.events.order_by('-created_at'),
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
        job.refresh_from_db()

    if request.htmx:
        return render(request, 'jobs/job_status_with_history.html', {
            'job': job,
            'events': job.events.order_by('-created_at'),
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


@login_required
def company_detail(request, uuid):
    company = get_object_or_404(Company, uuid=uuid)
    jobs = company.jobs.select_related('location').order_by('-date_posted')
    return render(request, 'companies/company_detail.html', {
        'company': company,
        'jobs': jobs,
    })


@login_required
def job_review(request):
    filter_status = request.GET.get('status', 'new')
    if filter_status not in ['new', 'saved']:
        filter_status = 'new'

    job = Job.objects.filter(status=filter_status).select_related('company', 'location').order_by('-date_posted').first()

    new_count = Job.objects.filter(status=Job.Status.NEW).count()
    saved_count = Job.objects.filter(status=Job.Status.SAVED).count()

    return render(request, 'jobs/job_review.html', {
        'job': job,
        'new_count': new_count,
        'saved_count': saved_count,
        'current_filter': filter_status,
    })


@login_required
def job_review_action(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    job = get_object_or_404(Job, uuid=uuid)
    new_status = request.POST.get('status')

    if new_status in Job.Status.values:
        job.update_status(new_status)

    filter_status = request.GET.get('filter', 'new')
    return redirect(f"{reverse('web:job_review')}?status={filter_status}")


@login_required
def company_toggle_ban(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    company = get_object_or_404(Company, uuid=uuid)

    if company.is_banned:
        company.unban()
    else:
        reason = request.POST.get('reason', '').strip()
        company.ban(reason)

    if request.htmx:
        jobs = company.jobs.select_related('location').order_by('-date_posted')
        return render(request, 'companies/company_ban_status.html', {'company': company, 'jobs': jobs, 'is_htmx': True})

    return redirect('web:company_detail', uuid=uuid)


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.save()

        timezone = request.POST.get('timezone', 'UTC')
        valid_timezones = [tz[0] for tz in get_timezone_choices()]
        if timezone in valid_timezones:
            profile.timezone = timezone
            profile.save()

        return redirect('web:profile')

    resumes = profile.resumes.all()
    timezone_choices = get_timezone_choices()

    return render(request, 'profile.html', {
        'profile': profile,
        'resumes': resumes,
        'timezone_choices': timezone_choices,
    })


@login_required
def resume_upload(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    name = request.POST.get('name', '').strip()
    file = request.FILES.get('file')

    if file:
        if not name:
            name = file.name
        resume = Resume.objects.create(user=profile, name=name, file=file)
        resume.extract_text()

        # If this is the only resume, make it the default
        if profile.resumes.count() == 1:
            profile.default_resume = resume
            profile.save()

    if request.htmx:
        resumes = profile.resumes.all()
        return render(request, 'profile_resumes.html', {'resumes': resumes, 'profile': profile})

    return redirect('web:profile')


@login_required
def resume_delete(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    resume = get_object_or_404(Resume, uuid=uuid, user=profile)

    if profile.default_resume == resume:
        profile.default_resume = None
        profile.save()

    resume.file.delete()
    resume.delete()

    if request.htmx:
        resumes = profile.resumes.all()
        return render(request, 'profile_resumes.html', {'resumes': resumes, 'profile': profile})

    return redirect('web:profile')


@login_required
def resume_set_default(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    resume = get_object_or_404(Resume, uuid=uuid, user=profile)

    profile.default_resume = resume
    profile.save()

    if request.htmx:
        resumes = profile.resumes.all()
        return render(request, 'profile_resumes.html', {'resumes': resumes, 'profile': profile})

    return redirect('web:profile')
