import logging
from typing import ClassVar
from urllib.parse import quote, urlencode, urlparse

from django.utils import timezone

from sisyphus.searches.models import Search
from sisyphus.searches.parsers.base import BaseParser
from sisyphus.searches.utils import NullableTag, remove_query

logger = logging.getLogger(__name__)


class LinkedInParser(BaseParser):
    JOBS_PER_PAGE = 10

    MAX_JOB_COUNT = 1000

    blocklist: ClassVar[list[str]] = [
        'static.licdn.com',
        'media.licdn.com',
        'li.protechts.net',
        'accounts.google.com',
        'client.protechts.net',
        'fonts.gstatic.com',
        'tzm.protechts.net',
    ]

    name = 'linkedin'

    def intercept_request(self, route):
        if super().intercept_request(route):
            return
        url = urlparse(route.request.url)
        if url.hostname == 'www.linkedin.com' and url.path.strip('/') in ['', 'authwall', 'favicon.ico']:
            route.abort()
        else:
            route.continue_()

    def get_linkedin_url(self, endpoint: str, search: Search, page: int = 1, period: int | None = None):
        params = {
            'keywords': quote(search.keywords),
            'geo_id': search.geo_id,
        }

        if search.easy_apply:
            params['f_AL'] = 'true'

        wt = [
            str(code)
            for value, code in [
                (search.is_onsite, 1),
                (search.is_remote, 2),
                (search.is_hybrid, 3),
            ]
            if value
        ]
        if wt:
            params['f_WT'] = quote(','.join(wt))

        if page > 1:
            params['start'] = self.JOBS_PER_PAGE * (page - 1)

        if period is not None:
            params['f_TPR'] = f'r{period}'

        # if location contains a comma set distance to 25 with the
        # assumption that names with commas represent cities in states
        if ',' in getattr(search.location, 'name', ''):
            params['distance'] = 25

        return f'https://www.linkedin.com{endpoint}search?{urlencode(params)}'

    def get_job_count(self, search: Search) -> int:
        """Return number of jobs found."""
        url = self.get_linkedin_url('/jobs/', search)
        tag = self.get(url)
        if not tag:
            logger.error('Unable to retrieve job count.')
            return 0
        
        try:
            tag = tag.find('span', {'class': 'results-context-header__job-count'})
            if not tag:
                logger.error('`results-context-header__job-count` not found.')
                return 0
            count = tag.get_text(strip=True)
            return min(int(''.join(filter(str.isdigit, count))), self.MAX_JOB_COUNT)
        except Exception:
            logger.exception('Error parsing job count.')
            return 0
        
    def get_page_count(self, search: Search) -> int:
        """Return number of pages to search."""
        count = self.get_job_count(search)
        if count == 0:
            return 1
        return (count // self.JOBS_PER_PAGE) + 1

    def parse_job(self, div: NullableTag) -> dict | None:
        """Parse job div."""
        error: str | None = None
        job = {}

        try:
            company_link = div.find('h4', {'class': 'base-search-card__subtitle'}).find('a')
            job['company'] = company_link.text
            url = company_link.get('href')
            job['company_url'] = remove_query(url)
        except Exception:
            logger.exception('Error parsing company information')
            error = 'company'

        try:
            job['title'] = div.find('h3', {'class': 'base-search-card__title'}).text
        except Exception:
            logger.exception('Error parsing job title')
            error = 'title'

        try:
            url = div.find('a', {'class': 'base-card__full-link'}).get('href')
            job['url'] = remove_query(url)
        except Exception:
            logger.exception('Error parsing job url')
            error = 'url'

        try:
            job['location'] = div.find('span', {'class': 'job-search-card__location'}).text
        except Exception:
            logger.exception('Unable to get location. Setting to None')
            job['location'] = None

        try:
            time = div.find('time', {'class': 'job-search-card__listdate'}) or div.find(
                'time', {'class': 'job-search-card__listdate--new'}
            )
            job['date_posted'] = time.get('datetime')
        except Exception:
            logger.exception('Error parsing job post date')
            error = 'date_posted'

        job['date_found'] = str(timezone.now())

        if error is not None:
            return None
        return job

    def parse(self, search: Search, page=1) -> list[dict]:
        """Parse jobs."""
        jobs: list[dict] = []
        period = search.calculate_period()

        url = self.get_linkedin_url('/jobs-guest/jobs/api/seeMoreJobPostings/', search, page, period)
        tag = self.get(url)
        if not tag:
            logger.warning('Response for %s is None', url)
            return jobs
        
        for div in tag.find_all('div', {'class': 'job-search-card'}):
            job = self.parse_job(NullableTag(div))
            if job is not None:
                jobs.append(job)
        return jobs
