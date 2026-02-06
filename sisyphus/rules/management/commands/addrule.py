from django.core.management.base import BaseCommand, CommandError

from sisyphus.accounts.models import User, UserProfile
from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule, RuleCondition


class Command(BaseCommand):
    help = 'Add a new rule with conditions'

    def add_arguments(self, parser):
        parser.add_argument('condition', type=str)
        parser.add_argument(
            '--status',
            type=str,
            default=Job.Status.FILTERED,
            choices=[s[0] for s in Job.Status.choices],
            help=f'Target status for matching jobs (default: {Job.Status.FILTERED})',
        )
        parser.add_argument('--user', type=str, required=True)

    def parse_condition(self, condition):
        for match_type in RuleCondition.MatchType.values:
            parts = condition.split(f'{match_type} ', 1)
            if len(parts) == 2:
                return parts[0].strip(), match_type, parts[1].strip()
        return None, None, None

    def handle(self, **options):
        field, match_type, value = self.parse_condition(options['condition'])
        if field not in RuleCondition.Field.values:
            raise CommandError('Invalid field.')
        if match_type is None:
            raise CommandError('Invalid match type.')

        try:
            user = User.objects.get(email=options['user'])
        except User.DoesNotExist:
            raise CommandError('User does not exist.')
        profile, _ = UserProfile.objects.get_or_create(user=user)

        status = options['status']
        priority = 10 if status == Job.Status.SAVED else 0

        # Check for duplicate rule
        conditions = [{'field': field, 'match_type': match_type, 'value': value}]
        duplicate = Rule.find_duplicate(profile, Rule.MatchMode.ALL, status, conditions)
        if duplicate:
            raise CommandError(f"A rule with these settings already exists: '{duplicate.name}'.")

        rule = Rule.objects.create(
            user=profile,
            name=value,
            match_mode=Rule.MatchMode.ALL,
            target_status=status,
            priority=priority,
        )
        RuleCondition.objects.create(
            rule=rule,
            field=field,
            match_type=match_type,
            value=value,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Created rule '{value}' with target status {rule.get_target_status_display()}")
        )
