import logging
import resource

from rq.worker import SimpleWorker

logger = logging.getLogger(__name__)

MAX_MEMORY_MB = 3072  # 3 GB


class MemoryLimitWorker(SimpleWorker):
    """RQ worker that shuts down gracefully when RSS exceeds MAX_MEMORY_MB."""

    def perform_job(self, job, queue):
        result = super().perform_job(job, queue)

        rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        logger.info('Worker RSS after job %s: %d MB', job.id, rss_mb)

        if rss_mb > MAX_MEMORY_MB:
            logger.warning(
                'Worker exceeded memory limit (%d MB > %d MB). Shutting down.',
                rss_mb,
                MAX_MEMORY_MB,
            )
            self._stop_requested = True

        return result
