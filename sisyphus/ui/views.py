from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as user_login, logout as user_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from sisyphus.jobs.models import Job


@login_required
def index(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        uuid = request.POST.get('uuid')
        job = Job.objects.get(uuid=uuid)
        job.update_status(action)

    actions = [
        {
            'text': 'Applied',
            'value': Job.APPLIED,
            'btn': 'success',
        },
        {
            'text': 'Expired',
            'value': Job.EXPIRED,
            'btn': 'warning',
        },
        {
            'text': 'Dismissed',
            'value': Job.DISMISSED,
            'btn': 'danger',
        },
        {
            'text': 'Save Job',
            'value': Job.SAVED,
            'btn': 'info',
        }
    ]
    job = Job.objects.next_job()
    return render(request, 'feed.html', {'actions': actions, 'job': job})


@login_required
def saved(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        uuid = request.POST.get('uuid')
        job = Job.objects.get(uuid=uuid)
        job.update_status(action)

    actions = [
        {
            'text': 'Applied',
            'value': Job.APPLIED,
            'btn': 'success',
        },
        {
            'text': 'Expired',
            'value': Job.EXPIRED,
            'btn': 'warning',
        },
        {
            'text': 'Dismissed',
            'value': Job.DISMISSED,
            'btn': 'danger',
        }
    ]
    job = Job.objects.next_job(True)
    return render(request, 'feed.html', {'actions': actions, 'job': job})


def login(request):
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            user_login(request, user)
            if next_url is not None:
                return redirect(next_url)
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html', {'next': next_url})


def logout(request):
    user_logout(request)
    return redirect(settings.LOGIN_URL)
