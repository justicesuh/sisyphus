from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

if TYPE_CHECKING:
    import uuid as uuid_mod

    from django.http import HttpRequest, HttpResponse

from sisyphus.companies.models import Company, CompanyNote

SORT_OPTIONS = {
    'name': 'name',
    '-name': '-name',
    'job_count': 'job_count',
    '-job_count': '-job_count',
}


@login_required
def company_list(request: HttpRequest) -> HttpResponse:
    """Display paginated list of companies."""
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
    if sort in SORT_OPTIONS:
        companies = companies.order_by(SORT_OPTIONS[sort])
    else:
        sort = 'name'
        companies = companies.order_by('name')

    paginator = Paginator(companies, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'companies/company_list.html',
        {
            'page': page,
            'current_search': search,
            'current_banned': banned,
            'current_sort': sort,
        },
    )


@login_required
def company_detail(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Display company detail page with jobs and notes."""
    company = get_object_or_404(Company, uuid=uuid)
    jobs = company.jobs.select_related('location').order_by('-date_posted')
    return render(
        request,
        'companies/company_detail.html',
        {
            'company': company,
            'jobs': jobs,
            'notes': company.notes.all(),
        },
    )


@login_required
def company_add_note(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Add a note to a company."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    company = get_object_or_404(Company, uuid=uuid)
    text = request.POST.get('text', '').strip()

    if text:
        company.add_note(text)

    if request.htmx:  # type: ignore[attr-defined]
        return render(
            request,
            'companies/company_notes_inner.html',
            {'company': company, 'notes': company.notes.all()},
        )

    return redirect('companies:company_detail', uuid=uuid)


@login_required
def company_delete_note(request: HttpRequest, uuid: uuid_mod.UUID, note_id: int) -> HttpResponse:
    """Delete a note from a company."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    note = get_object_or_404(CompanyNote, id=note_id, company__uuid=uuid)
    company = note.company
    note.delete()

    if request.htmx:  # type: ignore[attr-defined]
        return render(
            request,
            'companies/company_notes_inner.html',
            {'company': company, 'notes': company.notes.all()},
        )

    return redirect('companies:company_detail', uuid=uuid)


@login_required
def company_toggle_ban(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Toggle the banned status of a company."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    company = get_object_or_404(Company, uuid=uuid)

    if company.is_banned:
        company.unban()
    else:
        reason = request.POST.get('reason', '').strip()
        company.ban(reason)

    if request.htmx:  # type: ignore[attr-defined]
        jobs = company.jobs.select_related('location').order_by('-date_posted')
        return render(
            request,
            'companies/company_ban_status.html',
            {'company': company, 'jobs': jobs, 'is_htmx': True},
        )

    return redirect('companies:company_detail', uuid=uuid)
