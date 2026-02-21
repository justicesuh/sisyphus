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

    try:
        parser_cls = PARSERS.get(search.source.parser)
    except AttributeError:
        parser_cls = None
    if parser_cls is None:
        search.set_status(Search.Status.ERROR)
        return {'error': f'Unknown parser: {search.source.parser}'}

    search.set_status(Search.Status.RUNNING)
    period = search.calculate_period()
    run = SearchRun.objects.create(search=search, period=period)
    parser = parser_cls()

    try:
        if parser.name == 'hiringcafe':
            start = 0
            state = parser.generate_state(search, period)
            page_count = parser.get_page_count(state)
        else:
            start = 1
            page_count = parser.get_page_count(search)

        for page in range(start, page_count + 1):
            try:
                jobs = parser.parse(search, page=page, period=period)
                run.jobs_found += len(jobs)
                run.jobs_created += Job.objects.add_jobs(jobs, run)
            except Exception:
                break

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
    """Enqueue the search pipeline as chained jobs."""
    from rq import Callback  # noqa: PLC0415

    from sisyphus.searches.models import Search  # noqa: PLC0415

    search = Search.objects.get(id=search_id)
    if not search.is_active:
        return {'skipped': True, 'reason': 'Search is not active'}
    if search.status in (Search.Status.QUEUED, Search.Status.RUNNING):
        return {'skipped': True, 'reason': 'Search is already in progress'}

    search.set_status(Search.Status.QUEUED)

    queue = django_rq.get_queue()
    scrape_job = queue.enqueue(
        run_search,
        search_id,
        on_success=Callback(_on_scrape_success),
        on_failure=Callback(_on_scrape_failure),
        meta={'user_id': user_id, 'search_id': search_id},
    )

    return {'status': 'pipeline_started', 'scrape_job_id': scrape_job.id}


def _on_scrape_success(job, connection, result):
    """After run_search succeeds, enqueue the remaining pipeline steps."""
    from sisyphus.jobs.tasks import ban_jobs_with_banned_company  # noqa: PLC0415
    from sisyphus.rules.tasks import apply_all_rules  # noqa: PLC0415

    if 'error' in result:
        return

    user_id = job.meta['user_id']
    run_id = result['run_id']
    queue = django_rq.get_queue()

    rules_job = queue.enqueue(apply_all_rules, user_id)
    ban_job = queue.enqueue(ban_jobs_with_banned_company)
    queue.enqueue(populate_jobs, run_id, depends_on=[rules_job, ban_job])


def _on_scrape_failure(job, connection, typ, value, traceback):
    """Mark the search as errored if run_search fails."""
    from sisyphus.searches.models import Search  # noqa: PLC0415

    search_id = job.meta.get('search_id')
    if search_id:
        try:
            search = Search.objects.get(id=search_id)
            search.set_status(Search.Status.ERROR)
        except Search.DoesNotExist:
            pass


@django_rq.job
def populate_jobs(run_id: int) -> dict:
    """Enqueue individual populate tasks for each unpopulated job in a search run."""
    from sisyphus.jobs.models import Job  # noqa: PLC0415

    queue = django_rq.get_queue()
    job_ids = list(Job.objects.filter(search_run_id=run_id, populated=False).values_list('id', flat=True))

    for job_id in job_ids:
        queue.enqueue(populate_job, job_id)

    return {'run_id': run_id, 'enqueued': len(job_ids)}


@django_rq.job
def populate_job(job_id: int) -> dict:
    """Populate a single job's details from its source."""
    from sisyphus.jobs.models import Job  # noqa: PLC0415
    from sisyphus.searches.parsers import PARSERS  # noqa: PLC0415

    job = Job.objects.select_related('source').get(id=job_id)

    try:
        parser_cls = PARSERS.get(job.source.parser)
    except AttributeError:
        parser_cls = None
    if parser_cls is None:
        return {'error': f'Unknown parser: {job.source.parser}'}

    parser = parser_cls()
    parser.populate_job(job)

    return {'job_id': job_id}


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
