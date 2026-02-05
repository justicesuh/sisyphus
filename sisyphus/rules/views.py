from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from sisyphus.accounts.models import UserProfile
from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule, RuleCondition


@login_required
def rule_list(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rules = Rule.objects.filter(user=profile).prefetch_related('conditions')

    return render(request, 'rules/rule_list.html', {
        'rules': rules,
    })


@login_required
def rule_create(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        match_mode = request.POST.get('match_mode', Rule.MatchMode.ALL)
        target_status = request.POST.get('target_status', Job.Status.FILTERED)
        priority = int(request.POST.get('priority', 0))
        rule = Rule.objects.create(
            user=profile,
            name=name,
            match_mode=match_mode,
            target_status=target_status,
            priority=priority,
        )

        # Process conditions
        condition_count = int(request.POST.get('condition_count', 0))
        for i in range(condition_count):
            field = request.POST.get(f'condition_{i}_field')
            match_type = request.POST.get(f'condition_{i}_match_type')
            value = request.POST.get(f'condition_{i}_value', '').strip()

            if field and match_type and value:
                RuleCondition.objects.create(
                    rule=rule,
                    field=field,
                    match_type=match_type,
                    value=value,
                )

        return redirect('rules:rule_list')

    return render(request, 'rules/rule_form.html', {
        'match_mode_choices': Rule.MatchMode.choices,
        'status_choices': Job.Status.choices,
        'field_choices': RuleCondition.Field.choices,
        'match_type_choices': RuleCondition.MatchType.choices,
    })


@login_required
def rule_edit(request, uuid):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rule = get_object_or_404(Rule, uuid=uuid, user=profile)

    if request.method == 'POST':
        rule.name = request.POST.get('name', '').strip()
        rule.match_mode = request.POST.get('match_mode', Rule.MatchMode.ALL)
        rule.target_status = request.POST.get('target_status', Job.Status.FILTERED)
        rule.priority = int(request.POST.get('priority', 0))
        rule.save()

        # Delete existing conditions and recreate
        rule.conditions.all().delete()

        condition_count = int(request.POST.get('condition_count', 0))
        for i in range(condition_count):
            field = request.POST.get(f'condition_{i}_field')
            match_type = request.POST.get(f'condition_{i}_match_type')
            value = request.POST.get(f'condition_{i}_value', '').strip()

            if field and match_type and value:
                RuleCondition.objects.create(
                    rule=rule,
                    field=field,
                    match_type=match_type,
                    value=value,
                )

        return redirect('rules:rule_list')

    conditions = list(rule.conditions.all())

    return render(request, 'rules/rule_form.html', {
        'rule': rule,
        'conditions': conditions,
        'match_mode_choices': Rule.MatchMode.choices,
        'status_choices': Job.Status.choices,
        'field_choices': RuleCondition.Field.choices,
        'match_type_choices': RuleCondition.MatchType.choices,
    })


@login_required
def rule_delete(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rule = get_object_or_404(Rule, uuid=uuid, user=profile)
    rule.delete()

    if request.htmx:
        rules = Rule.objects.filter(user=profile).prefetch_related('conditions')
        return render(request, 'rules/rule_list_inner.html', {'rules': rules})

    return redirect('rules:rule_list')


@login_required
def rule_toggle(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rule = get_object_or_404(Rule, uuid=uuid, user=profile)
    rule.is_active = not rule.is_active
    rule.save(update_fields=['is_active'])

    if request.htmx:
        rules = Rule.objects.filter(user=profile).prefetch_related('conditions')
        return render(request, 'rules/rule_list_inner.html', {'rules': rules})

    return redirect('rules:rule_list')


@login_required
def rule_apply(request, uuid):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    rule = get_object_or_404(Rule, uuid=uuid, user=profile)

    from sisyphus.rules.tasks import apply_rule_to_existing_jobs
    apply_rule_to_existing_jobs.delay(rule.id)

    if request.htmx:
        rules = Rule.objects.filter(user=profile).prefetch_related('conditions')
        return render(request, 'rules/rule_list_inner.html', {
            'rules': rules,
            'message': f'Rule "{rule.name}" is being applied to existing jobs.',
        })

    return redirect('rules:rule_list')
