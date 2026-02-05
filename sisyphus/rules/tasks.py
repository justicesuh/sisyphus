from celery import shared_task


@shared_task
def apply_rule_to_existing_jobs(rule_id):
    from sisyphus.jobs.models import Job
    from sisyphus.rules.models import Rule, RuleMatch

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

            RuleMatch.objects.create(
                rule=rule,
                job=job,
                old_status=old_status,
                new_status=rule.target_status
            )
            matched_count += 1

    return {'matched_count': matched_count}
