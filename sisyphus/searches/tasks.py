import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
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


@shared_task
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

    try:
        for job in Job.objects.filter(search_run=run, populated=False):
            parser.populate_job(job)
            populated += 1
    finally:
        parser.close()

    return {
        'run_id': run_id,
        'populated': populated,
    }
