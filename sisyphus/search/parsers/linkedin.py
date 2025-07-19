import logging

from sisyphus.jobs.models import Job
from sisyphus.search.models import Search
from sisyphus.search.parsers.base import BaseParser


logger = logging.getLogger(__name__)


class LinkedInParser(BaseParser):
    MAX_JOB_COUNT = 1000

    JOBS_PER_PAGE = 10

    blocklist = [
        'accounts.google.com',
        'dpm.demdex.net',
        'fonts.gstatic.com',
        'platform.linkedin.com',
        'ponf.linkedin.com',
        'static.licdn.com',
        'trkn.us',
    ]

    def intercept_request(self, request):
        super().intercept_request(request)
        if request.response is not None and request.response.status_code == 404:
            return
        if request.host == 'www.linkedin.com' and request.path.strip('/') in ['', 'authwall', 'favicon.ico']:
            request.abort(error_code=404)

    def process_response(self, requests):
        for request in reversed(requests):
            if request.url.startswith('https://www.linkedin.com/jobs') and request.response is not None:
                return request.response
        return None

    def get_linkedin_url(self, endpoint, search: Search, page=1):
        url = 'https://linkedin.com{}search?keywords={}&geo_id={}'
        url = url.format(endpoint, search.keywords.replace(' ', '%20'), search.geo_id)

        if search.easy_apply:
            url = f'{url}&f_AL=true'

        wt = None
        if search.flexibility == Job.ONSITE:
            wt = 1
        elif search.flexibility == Job.REMOTE:
            wt = 2
        elif search.flexibility == Job.HYBRID:
            wt = 3
        if wt is not None:
            url = f'{url}&f_WT={wt}'

        if search.period is not None:
            url = f'{url}&f_TPR=r{search.period}'

        start = 10 * (page - 1)
        url = f'{url}&start={start}'

        return url

    def get_job_count(self, search: Search):
        url = self.get_linkedin_url('/jobs/', search)
        response = self.firefox.get_with_retry(url, retries=4)
        if response is None:
            logger.error('Unable to retrieve job count.')
            return 0

        soup = self.firefox.soupify()
        try:
            count = soup.find('span', {'class': 'results-context-header__job-count'}).text.strip()
            return min(int(count.replace(',', '').replace('+', '')), self.MAX_JOB_COUNT)
        except Exception:
            logger.error('Error parsing job count.')
            return 0

    def get_page_count(self, search: Search):
        count = self.get_job_count(search)
        if count == 0:
            logger.info('Setting page count to 1.')
            return 1
        return (count // self.JOBS_PER_PAGE) + 1
