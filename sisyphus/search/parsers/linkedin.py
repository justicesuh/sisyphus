import logging
from datetime import datetime

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

    def parse_job(self, div) -> dict | None:
        error = None
        job = {}

        try:
            company_link = div.find('h4', {'class': 'base-search-card__subtitle'}).find('a')
            job['company'] = company_link.text.strip()
            url = company_link['href']
            if '?' in url:
                url = url.split('?', 1)[0]
            job['company_url'] = url
        except Exception:
            error = 'company'
            logger.error('Error parsing company information.')

        try:
            job['title'] = div.find('h3', {'class': 'base-search-card__title'}).text.strip()
        except Exception:
            error = 'title'
            logger.error('Error parsing job title.')

        try:
            url = div.find('a', {'class': 'base-card__full-link'})['href']
            if '?' in url:
                url = url.split('?', 1)[0]
            sindex = url.rindex('/')
            dindex = url.rindex('-')
            job['url'] = url[:sindex + 1] + url[dindex + 1:] + '/'
        except Exception:
            error = 'url'
            logger.error('Error parsing job url.')

        try:
            job['location'] = div.find('span', {'class': 'job-search-card__location'}).text.strip()
        except Exception:
            job['location'] = None

        try:
            time = div.find('time', {'class': 'job-search-card__listdate'})
            if time is None:
                time = div.find('time', {'class': 'job-search-card__listdate--new'})
            job['date_posted'] = time['datetime']
        except Exception:
            error = 'date_posted'
            logger.error('Error parsing job post date.')

        job['date_found'] = datetime.now().strftime('%Y-%m-%d')

        if error is not None:
            return None
        return job

    def parse(self, search: Search, page=1) -> list[dict]:
        jobs = []

        url = self.get_linkedin_url('/jobs-guest/jobs/api/seeMoreJobPostings/', search, page)
        response = self.firefox.get_with_retry(url)
        if response is None:
            logger.info(f'Response for {url} is None.')
            return jobs

        for div in self.firefox.soupify().find_all('div', {'class': 'job-search-card'}):
            job = self.parse_job(div)
            if job is not None:
                jobs.append(job)

        return jobs

    def populate_job(self, job: Job):
        response = self.firefox.get_with_retry(job.url)
        if response is None:
            logger.info(f'Response for {job.url} is None.')
            if self.firefox.last_status_code == 404:
                logger.info('Job not found, marking as dismissed.')
                job.dismiss('Job not found.')
            return

        soup = self.firefox.soupify()
        job.raw_html = str(soup)

        try:
            job.description = soup.find('div', {'class': 'show-more-less-html__markup'}).decode_contents().strip()
        except Exception:
            logger.error('Error parsing job description.')

        try:
            code = soup.find('code', {'id': 'applyUrl'})
            if code is not None:
                job.easy_apply = False
            else:
                job.easy_apply = True
        except Exception:
            logger.warn('Failed to parse easy application status, Defaulting to False.')
            job.easy_apply = False

        job.populated = True
        job.save()
