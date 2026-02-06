from typing import Any

from celery import shared_task


@shared_task
def apply_all_rules(user_id: int) -> dict[str, Any]:
    """Apply all active rules for a user to eligible jobs."""
    from sisyphus.accounts.models import UserProfile  # noqa: PLC0415
    from sisyphus.jobs.models import Job  # noqa: PLC0415
    from sisyphus.rules.models import Rule, RuleMatch  # noqa: PLC0415

    try:
        profile = UserProfile.objects.get(id=user_id)
    except UserProfile.DoesNotExist:
        return {'error': 'User not found'}

    rules = Rule.objects.filter(user=profile, is_active=True).prefetch_related('conditions').order_by('-priority')
    jobs = Job.objects.filter(status__in=[Job.Status.NEW, Job.Status.SAVED], populated=True)

    matched_count = 0
    for job in jobs:
        for rule in rules:
            if rule.matches(job):
                old_status = job.status
                job.update_status(rule.target_status)

                RuleMatch.objects.create(rule=rule, job=job, old_status=old_status, new_status=rule.target_status)
                matched_count += 1
                break  # Only apply first matching rule per job

    return {'matched_count': matched_count}


@shared_task
def apply_rule_to_existing_jobs(rule_id: int) -> dict[str, Any]:
    """Apply a single rule to all eligible jobs."""
    from sisyphus.jobs.models import Job  # noqa: PLC0415
    from sisyphus.rules.models import Rule, RuleMatch  # noqa: PLC0415

    try:
        rule = Rule.objects.prefetch_related('conditions').get(id=rule_id)
    except Rule.DoesNotExist:
        return {'error': 'Rule not found'}

    if not rule.is_active:
        return {'skipped': True, 'reason': 'Rule is not active'}

    jobs = Job.objects.filter(status__in=[Job.Status.NEW, Job.Status.SAVED])
    matched_count = 0

    for job in jobs:
        if rule.matches(job):
            old_status = job.status
            job.update_status(rule.target_status)

            RuleMatch.objects.create(rule=rule, job=job, old_status=old_status, new_status=rule.target_status)
            matched_count += 1

    return {'matched_count': matched_count}
