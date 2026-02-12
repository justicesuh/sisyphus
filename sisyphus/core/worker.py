import logging
import os

from rq.worker import SimpleWorker

logger = logging.getLogger(__name__)

MAX_MEMORY_MB = 3072  # 3 GB


def _get_current_rss_mb() -> int:
    """Read current RSS from /proc/self/status (VmRSS line, in kB)."""
    with open('/proc/self/status') as f:
        for line in f:
            if line.startswith('VmRSS:'):
                return int(line.split()[1]) // 1024
    return 0


class MemoryLimitWorker(SimpleWorker):
    """RQ worker that shuts down gracefully when RSS exceeds MAX_MEMORY_MB."""

    def perform_job(self, job, queue):
        result = super().perform_job(job, queue)

        rss_mb = _get_current_rss_mb()
        logger.info('Worker RSS after job %s: %d MB', job.id, rss_mb)

        if rss_mb > MAX_MEMORY_MB:
            logger.warning(
                'Worker exceeded memory limit (%d MB > %d MB). Shutting down.',
                rss_mb,
                MAX_MEMORY_MB,
            )
            self._stop_requested = True

        return result
