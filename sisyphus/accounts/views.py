from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render

if TYPE_CHECKING:
    from sisyphus.core.types import AuthedHttpRequest, HtmxHttpRequest

from sisyphus.accounts.models import UserProfile, get_timezone_choices
from sisyphus.resumes.models import Resume


@login_required
def profile(request: AuthedHttpRequest) -> HttpResponse:
    """Display and update the user's profile."""
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.save()

        timezone = request.POST.get('timezone', 'UTC')
        valid_timezones = [tz[0] for tz in get_timezone_choices()]
        if timezone in valid_timezones:
            user_profile.timezone = timezone

        try:
            goal = int(request.POST.get('daily_application_goal', 0))
        except (TypeError, ValueError):
            goal = 0
        user_profile.daily_application_goal = max(goal, 0)

        user_profile.save()

        return redirect('accounts:profile')

    resume = getattr(user_profile, 'resume', None)
    timezone_choices = get_timezone_choices()

    return render(
        request,
        'profile.html',
        {
            'profile': user_profile,
            'resume': resume,
            'timezone_choices': timezone_choices,
        },
    )


@login_required
def resume_upload(request: HtmxHttpRequest) -> HttpResponse:
    """Handle resume file upload."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    name = request.POST.get('name', '').strip()
    file = request.FILES.get('file')

    if file:
        if not name:
            name = file.name or ''

        # Delete existing resume if one exists
        if hasattr(user_profile, 'resume'):
            user_profile.resume.file.delete()
            user_profile.resume.delete()

        resume = Resume.objects.create(user=user_profile, name=name, file=file)
        resume.extract_text()

    if request.htmx:
        current_resume: Resume | None = getattr(user_profile, 'resume', None)
        return render(request, 'profile_resumes.html', {'resume': current_resume})

    return redirect('accounts:profile')


@login_required
def resume_delete(request: HtmxHttpRequest) -> HttpResponse:
    """Handle resume deletion."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if hasattr(user_profile, 'resume'):
        user_profile.resume.file.delete()
        user_profile.resume.delete()

    if request.htmx:
        return render(request, 'profile_resumes.html', {'resume': None})

    return redirect('accounts:profile')
