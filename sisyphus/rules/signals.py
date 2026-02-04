from django.db.models.signals import post_save
from django.dispatch import receiver

from sisyphus.jobs.models import Job
from sisyphus.rules.services import apply_rules_to_job


@receiver(post_save, sender=Job)
def apply_rules_on_job_save(sender, instance, created, **kwargs):
    """
    Apply rules when a job is created or when populated becomes True.
    Only applies to jobs with NEW status.
    """
    if instance.status != Job.Status.NEW:
        return

    # Apply rules on creation
    if created:
        apply_rules_to_job(instance)
        return

    # Apply rules when job becomes populated
    update_fields = kwargs.get('update_fields')
    if update_fields and 'populated' in update_fields and instance.populated:
        apply_rules_to_job(instance)
