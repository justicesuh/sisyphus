from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule, RuleMatch


def apply_rules_to_job(job):
    """
    Apply all active rules to a job in priority order.
    Only applies to jobs with NEW status.
    Returns the RuleMatch if a rule matched and changed status, None otherwise.
    """
    if job.status != Job.Status.NEW:
        return None

    rules = Rule.objects.filter(
        is_active=True
    ).prefetch_related('conditions').order_by('-priority', 'name')

    for rule in rules:
        if rule.matches(job):
            old_status = job.status
            job.update_status(rule.target_status)

            rule_match = RuleMatch.objects.create(
                rule=rule,
                job=job,
                old_status=old_status,
                new_status=rule.target_status
            )
            return rule_match

    return None
