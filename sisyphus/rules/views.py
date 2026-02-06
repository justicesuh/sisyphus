from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

if TYPE_CHECKING:
    import uuid as uuid_mod

    from django.http import HttpRequest, HttpResponse

from sisyphus.accounts.models import UserProfile
from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule, RuleCondition


@login_required
def rule_list(request: HttpRequest) -> HttpResponse:
    """Display paginated list of rules."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rules = Rule.objects.filter(user=profile).prefetch_related('conditions')

    paginator = Paginator(rules, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'rules/rule_list.html',
        {
            'page': page,
        },
    )


def _parse_conditions_from_post(request: HttpRequest) -> list[dict[str, str]]:
    """Parse conditions from POST data."""
    conditions = []
    condition_count = int(request.POST.get('condition_count', 0))
    for i in range(condition_count):
        field = request.POST.get(f'condition_{i}_field')
        match_type = request.POST.get(f'condition_{i}_match_type')
        value = request.POST.get(f'condition_{i}_value', '').strip()

        if field and match_type and value:
            conditions.append(
                {
                    'field': field,
                    'match_type': match_type,
                    'value': value,
                }
            )
    return conditions


@login_required
def rule_create(request: HttpRequest) -> HttpResponse:
    """Create a new rule."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        match_mode = request.POST.get('match_mode', Rule.MatchMode.ALL)
        target_status = request.POST.get('target_status', Job.Status.FILTERED)
        priority = int(request.POST.get('priority', 0))

        conditions = _parse_conditions_from_post(request)

        # Check for duplicate rule
        duplicate = Rule.find_duplicate(profile, match_mode, target_status, conditions)
        if duplicate:
            return render(
                request,
                'rules/rule_form.html',
                {
                    'error': f'A rule with these settings already exists: "{duplicate.name}"',
                    'match_mode_choices': Rule.MatchMode.choices,
                    'status_choices': Job.Status.choices,
                    'field_choices': RuleCondition.Field.choices,
                    'match_type_choices': RuleCondition.MatchType.choices,
                    'form_data': {
                        'name': name,
                        'match_mode': match_mode,
                        'target_status': target_status,
                        'priority': priority,
                    },
                    'conditions': [type('Condition', (), c)() for c in conditions],
                },
            )

        rule = Rule.objects.create(
            user=profile,
            name=name,
            match_mode=match_mode,
            target_status=target_status,
            priority=priority,
        )

        for condition in conditions:
            RuleCondition.objects.create(rule=rule, **condition)

        return redirect('rules:rule_list')

    return render(
        request,
        'rules/rule_form.html',
        {
            'match_mode_choices': Rule.MatchMode.choices,
            'status_choices': Job.Status.choices,
            'field_choices': RuleCondition.Field.choices,
            'match_type_choices': RuleCondition.MatchType.choices,
        },
    )


@login_required
def rule_edit(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Edit an existing rule."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rule = get_object_or_404(Rule, uuid=uuid, user=profile)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        match_mode = request.POST.get('match_mode', Rule.MatchMode.ALL)
        target_status = request.POST.get('target_status', Job.Status.FILTERED)
        priority = int(request.POST.get('priority', 0))

        conditions = _parse_conditions_from_post(request)

        # Check for duplicate rule (excluding current rule)
        duplicate = Rule.find_duplicate(profile, match_mode, target_status, conditions, exclude_rule=rule)
        if duplicate:
            return render(
                request,
                'rules/rule_form.html',
                {
                    'rule': rule,
                    'error': f'A rule with these settings already exists: "{duplicate.name}"',
                    'match_mode_choices': Rule.MatchMode.choices,
                    'status_choices': Job.Status.choices,
                    'field_choices': RuleCondition.Field.choices,
                    'match_type_choices': RuleCondition.MatchType.choices,
                    'conditions': [type('Condition', (), c)() for c in conditions],
                },
            )

        rule.name = name
        rule.match_mode = match_mode
        rule.target_status = target_status
        rule.priority = priority
        rule.save()

        # Delete existing conditions and recreate
        rule.conditions.all().delete()
        for condition in conditions:
            RuleCondition.objects.create(rule=rule, **condition)

        return redirect('rules:rule_list')

    conditions = list(rule.conditions.all())

    return render(
        request,
        'rules/rule_form.html',
        {
            'rule': rule,
            'conditions': conditions,
            'match_mode_choices': Rule.MatchMode.choices,
            'status_choices': Job.Status.choices,
            'field_choices': RuleCondition.Field.choices,
            'match_type_choices': RuleCondition.MatchType.choices,
        },
    )


@login_required
def rule_delete(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Delete a rule."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rule = get_object_or_404(Rule, uuid=uuid, user=profile)
    rule.delete()

    if request.htmx:
        rules = Rule.objects.filter(user=profile).prefetch_related('conditions')
        paginator = Paginator(rules, 25)
        page = paginator.get_page(1)
        return render(request, 'rules/rule_list_inner.html', {'page': page})

    return redirect('rules:rule_list')


@login_required
def rule_toggle(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Toggle a rule's active status."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rule = get_object_or_404(Rule, uuid=uuid, user=profile)
    rule.is_active = not rule.is_active
    rule.save(update_fields=['is_active'])

    if request.htmx:
        rules = Rule.objects.filter(user=profile).prefetch_related('conditions')
        paginator = Paginator(rules, 25)
        page = paginator.get_page(1)
        return render(request, 'rules/rule_list_inner.html', {'page': page})

    return redirect('rules:rule_list')


@login_required
def rule_apply(request: HttpRequest, uuid: uuid_mod.UUID) -> HttpResponse:
    """Apply a rule to all existing jobs."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rule = get_object_or_404(Rule, uuid=uuid, user=profile)

    from sisyphus.rules.tasks import apply_rule_to_existing_jobs  # noqa: PLC0415

    apply_rule_to_existing_jobs.delay(rule.id)

    if request.htmx:
        rules = Rule.objects.filter(user=profile).prefetch_related('conditions')
        paginator = Paginator(rules, 25)
        page = paginator.get_page(1)
        return render(
            request,
            'rules/rule_list_inner.html',
            {
                'page': page,
                'message': f'Rule "{rule.name}" is being applied to existing jobs.',
            },
        )

    return redirect('rules:rule_list')


@login_required
def rule_apply_all(request: HttpRequest) -> HttpResponse:
    """Apply all active rules to existing jobs."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    from sisyphus.rules.tasks import apply_all_rules  # noqa: PLC0415

    apply_all_rules.delay(profile.id)

    if request.htmx:
        rules = Rule.objects.filter(user=profile).prefetch_related('conditions')
        paginator = Paginator(rules, 25)
        page = paginator.get_page(1)
        return render(
            request,
            'rules/rule_list_inner.html',
            {
                'page': page,
                'message': 'All rules are being applied to existing jobs.',
            },
        )

    return redirect('rules:rule_list')
