from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

if TYPE_CHECKING:
    import uuid as uuid_mod

    from django.http import HttpRequest, HttpResponse

from sisyphus.accounts.models import UserProfile
from sisyphus.jobs.models import Location
from sisyphus.searches.models import Search, Source

SORT_OPTIONS = {
    'keywords': 'keywords',
    '-keywords': '-keywords',
    'last_executed_at': 'last_executed_at',
    '-last_executed_at': '-last_executed_at',
}


@login_required
def search_list(request: HttpRequest) -> HttpResponse:
    """Display paginated list of searches."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    searches = Search.objects.filter(user=profile).select_related('source', 'location')

    q = request.GET.get('q', '').strip()
    if q:
        searches = searches.filter(Q(keywords__icontains=q))

    status = request.GET.get('status', '')
    if status:
        searches = searches.filter(status=status)

    active = request.GET.get('active', '')
    if active == 'yes':
        searches = searches.filter(is_active=True)
    elif active == 'no':
        searches = searches.filter(is_active=False)

    sort = request.GET.get('sort', 'keywords')
    if sort in SORT_OPTIONS:
        searches = searches.order_by(SORT_OPTIONS[sort])
    else:
        sort = 'keywords'
        searches = searches.order_by('keywords')

    paginator = Paginator(searches, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'searches/search_list.html',
        {
            'page': page,
            'current_search': q,
            'current_status': status,
            'current_active': active,
            'current_sort': sort,
            'status_choices': Search.Status.choices,
        },
    )


@login_required
def search_create(request: HttpRequest) -> HttpResponse:
    """Create a new search."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        keywords = request.POST.get('keywords', '').strip()
        source_id = request.POST.get('source', '')
        location_id = request.POST.get('location', '')
        easy_apply = request.POST.get('easy_apply') == 'on'
        is_hybrid = request.POST.get('is_hybrid') == 'on'
        is_onsite = request.POST.get('is_onsite') == 'on'
        is_remote = request.POST.get('is_remote') == 'on'
        schedule = request.POST.get('schedule', '').strip()

        form_data = {
            'keywords': keywords,
            'source': source_id,
            'location': location_id,
            'easy_apply': easy_apply,
            'is_hybrid': is_hybrid,
            'is_onsite': is_onsite,
            'is_remote': is_remote,
            'schedule': schedule,
        }

        if not keywords or not source_id:
            return render(
                request,
                'searches/search_form.html',
                {
                    'error': 'Keywords and source are required.',
                    'sources': Source.objects.all(),
                    'locations': Location.objects.all(),
                    'form_data': form_data,
                },
            )

        duplicate = Search.find_duplicate(
            user=profile,
            keywords=keywords,
            source_id=source_id,
            location_id=location_id or None,
        )
        if duplicate:
            return render(
                request,
                'searches/search_form.html',
                {
                    'error': f'A search with these keywords, source, and location already exists: "{duplicate.keywords}"',
                    'sources': Source.objects.all(),
                    'locations': Location.objects.all(),
                    'form_data': form_data,
                },
            )

        search = Search.objects.create(
            user=profile,
            keywords=keywords,
            source_id=source_id,
            location_id=location_id or None,
            easy_apply=easy_apply,
            is_hybrid=is_hybrid,
            is_onsite=is_onsite,
            is_remote=is_remote,
            schedule=schedule,
        )
        search.sync_schedule()

        return redirect('searches:search_list')

    return render(
        request,
        'searches/search_form.html',
        {
            'sources': Source.objects.all(),
            'locations': Location.objects.all(),
        },
    )


@login_required
def search_edit(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Edit an existing search."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    search = get_object_or_404(Search.objects.select_related('source', 'location'), uuid=uuid, user=profile)

    if request.method == 'POST':
        keywords = request.POST.get('keywords', '').strip()
        source_id = request.POST.get('source', '')
        location_id = request.POST.get('location', '')
        easy_apply = request.POST.get('easy_apply') == 'on'
        is_hybrid = request.POST.get('is_hybrid') == 'on'
        is_onsite = request.POST.get('is_onsite') == 'on'
        is_remote = request.POST.get('is_remote') == 'on'
        schedule = request.POST.get('schedule', '').strip()

        if not keywords or not source_id:
            return render(
                request,
                'searches/search_form.html',
                {
                    'search': search,
                    'error': 'Keywords and source are required.',
                    'sources': Source.objects.all(),
                    'locations': Location.objects.all(),
                },
            )

        duplicate = Search.find_duplicate(
            user=profile,
            keywords=keywords,
            source_id=source_id,
            location_id=location_id or None,
            exclude_search=search,
        )
        if duplicate:
            return render(
                request,
                'searches/search_form.html',
                {
                    'search': search,
                    'error': f'A search with these keywords, source, and location already exists: "{duplicate.keywords}"',
                    'sources': Source.objects.all(),
                    'locations': Location.objects.all(),
                },
            )

        search.keywords = keywords
        search.source_id = source_id
        search.location_id = location_id or None
        search.easy_apply = easy_apply
        search.is_hybrid = is_hybrid
        search.is_onsite = is_onsite
        search.is_remote = is_remote
        search.schedule = schedule
        search.save()
        search.sync_schedule()

        return redirect('searches:search_detail', uuid=search.uuid)

    return render(
        request,
        'searches/search_form.html',
        {
            'search': search,
            'sources': Source.objects.all(),
            'locations': Location.objects.all(),
        },
    )


@login_required
def search_detail(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Display search detail page with recent runs."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    search = get_object_or_404(Search.objects.select_related('source', 'location'), uuid=uuid, user=profile)
    runs = search.runs.all()[:10]
    return render(
        request,
        'searches/search_detail.html',
        {
            'search': search,
            'runs': runs,
        },
    )


@login_required
def search_toggle(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Toggle a search's active status."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    search = get_object_or_404(Search, uuid=uuid, user=profile)
    search.is_active = not search.is_active
    search.save(update_fields=['is_active'])
    search.sync_schedule()

    return redirect('searches:search_list')


@login_required
def search_delete(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Delete a search."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    search = get_object_or_404(Search, uuid=uuid, user=profile)
    search.schedule = ''
    search.sync_schedule()
    search.delete()

    return redirect('searches:search_list')
