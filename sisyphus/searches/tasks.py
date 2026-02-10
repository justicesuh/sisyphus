import logging

import django_rq
from django.utils import timezone

logger = logging.getLogger(__name__)


@django_rq.job
def run_search(search_id: int) -> dict:
    """Execute a search using its source's parser."""
    from sisyphus.jobs.models import Job  # noqa: PLC0415
    from sisyphus.searches.models import Search, SearchRun  # noqa: PLC0415
    from sisyphus.searches.parsers import PARSERS  # noqa: PLC0415

    search = Search.objects.select_related('source', 'location').get(id=search_id)

    parser_cls = PARSERS.get(search.source.parser)
    if parser_cls is None:
        search.set_status(Search.Status.ERROR)
        return {'error': f'Unknown parser: {search.source.parser}'}

    search.set_status(Search.Status.RUNNING)
    period = search.calculate_period()
    run = SearchRun.objects.create(search=search, period=period)
    parser = parser_cls()

    try:
        page_count = parser.get_page_count(search)

        for page in range(1, page_count + 1):
            jobs = parser.parse(search, page=page, period=period)
            run.jobs_found += len(jobs)
            run.jobs_created += Job.objects.add_jobs(jobs, run)

        run.status = SearchRun.Status.SUCCESS
        search.set_status(Search.Status.SUCCESS)
    except Exception as exc:
        logger.exception('Search %s failed', search_id)
        run.status = SearchRun.Status.ERROR
        run.error_message = str(exc)
        search.set_status(Search.Status.ERROR)
        raise
    finally:
        run.completed_at = timezone.now()
        run.save()
        parser.close()

    return {
        'search_id': search_id,
        'run_id': run.id,
        'jobs_found': run.jobs_found,
        'jobs_created': run.jobs_created,
    }


@django_rq.job
def execute_search(search_id: int, user_id: int) -> dict:
    """Run a full search pipeline: scrape, apply rules, populate, apply rules, score."""
    from sisyphus.jobs.tasks import ban_jobs_with_banned_company
    from sisyphus.rules.tasks import apply_all_rules  # noqa: PLC0415
    from sisyphus.searches.models import Search  # noqa: PLC0415

    search = Search.objects.get(id=search_id)
    if not search.is_active:
        return {'skipped': True, 'reason': 'Search is not active'}
    if search.status in (Search.Status.QUEUED, Search.Status.RUNNING):
        return {'skipped': True, 'reason': 'Search is already in progress'}

    search.set_status(Search.Status.QUEUED)
    result = run_search(search_id)
    if 'error' in result:
        return result

    apply_all_rules(user_id)
    ban_jobs_with_banned_company()
    populate_jobs(result['run_id'])
    # apply_all_rules(user_id)
    score_new_jobs(result['run_id'], user_id)

    return result


@django_rq.job
def populate_jobs(run_id: int) -> dict:
    """Populate unpopulated jobs for a search run."""
    from sisyphus.jobs.models import Job  # noqa: PLC0415
    from sisyphus.searches.models import SearchRun  # noqa: PLC0415
    from sisyphus.searches.parsers import PARSERS  # noqa: PLC0415

    run = SearchRun.objects.select_related('search__source').get(id=run_id)

    parser_cls = PARSERS.get(run.search.source.parser)
    if parser_cls is None:
        return {'error': f'Unknown parser: {run.search.source.parser}'}

    parser = parser_cls()
    populated = 0

    for job in Job.objects.filter(search_run=run, populated=False):
        try:
            parser.populate_job(job)
            populated += 1
        except Exception:
            pass

    parser.close()

    return {
        'run_id': run_id,
        'populated': populated,
    }


def score_new_jobs(run_id: int, user_id: int) -> dict:
    """Score remaining new jobs in a search run against the user's resume."""
    from sisyphus.accounts.models import UserProfile  # noqa: PLC0415
    from sisyphus.jobs.models import Job  # noqa: PLC0415
    from sisyphus.resumes.models import Resume  # noqa: PLC0415

    try:
        profile = UserProfile.objects.get(id=user_id)
    except UserProfile.DoesNotExist:
        return {'error': 'User not found'}

    try:
        resume = Resume.objects.get(user=profile)
    except Resume.DoesNotExist:
        return {'skipped': True, 'reason': 'No resume found'}

    jobs = Job.objects.filter(search_run_id=run_id, status=Job.Status.NEW, populated=True)
    scored = 0
    for job in jobs:
        try:
            if job.calculate_score(resume) is not None:
                scored += 1
        except Exception:
            pass

    return {'run_id': run_id, 'scored': scored}
