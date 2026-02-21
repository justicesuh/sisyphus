import base64
import logging
import json
from datetime import datetime
from typing import ClassVar
from urllib.parse import urlencode

from django.utils import timezone

from sisyphus.searches.models import Search
from sisyphus.searches.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class HiringCafeParser(BaseParser):
    JOBS_PER_PAGE = 40

    blocklist: ClassVar[list[str]] = []

    name = 'hiringcafe'

    search_state = {
        'locations': [
            {
                'formatted_address': 'United States',
                'types': ['country'],
                'id': 'user_country',
                'address_components': [{'long_name': 'United States', 'short_name': 'US', 'types': ['country']}],
                'options': {'flexible_regions': ['anywhere_in_continent']}
            }
        ],
        'workplaceTypes': ['Remote'],
        'defaultToUserLocation': False,
        'userLocation': None,
        'physicalEnvironments': ['Office', 'Outdoor', 'Vehicle', 'Industrial', 'Customer-Facing'],
        'physicalLaborIntensity': ['Low', 'Medium', 'High'],
        'physicalPositions': ['Sitting', 'Standing'],
        'oralCommunicationLevels': ['Low', 'Medium', 'High'],
        'computerUsageLevels': ['Low', 'Medium', 'High'],
        'cognitiveDemandLevels': ['Low', 'Medium', 'High'],
        'currency': {'label': 'Any', 'value': None},
        'frequency': {'label': 'Any', 'value': None},
        'minCompensationLowEnd': None,
        'minCompensationHighEnd': None,
        'maxCompensationLowEnd': None,
        'maxCompensationHighEnd': None,
        'restrictJobsToTransparentSalaries': False,
        'calcFrequency': 'Yearly',
        'commitmentTypes': ['Full Time', 'Part Time', 'Contract', 'Internship', 'Temporary', 'Seasonal', 'Volunteer'],
        'jobTitleQuery': '',
        'jobDescriptionQuery': '',
        'excludeAllLicensesAndCertifications': False,
        'seniorityLevel': ['No Prior Experience Required', 'Entry Level' 'Mid Level', 'Senior Level'],
        'roleTypes': ['Individual Contributor', 'People Manager'],
        'roleYoeRange': [0, 20],
        'excludeIfRoleYoeIsNotSpecified': False,
        'managementYoeRange': [0, 20],
        'excludeIfManagementYoeIsNotSpecified': False,
        'securityClearances': ['None', 'Confidential', 'Secret', 'Top Secret', 'Top Secret/SCI', 'Public Trust', 'Interim Clearances', 'Other'],
        'excludeJobsWithAdditionalLanguageRequirements': False,
        'airTravelRequirement': ['None', 'Minimal', 'Moderate', 'Extensive'],
        'landTravelRequirement': ['None', 'Minimal', 'Moderate', 'Extensive'],
        'weekendAvailabilityRequired': 'Doesn\'t Matter',
        'holidayAvailabilityRequired': 'Doesn\'t Matter',
        'overtimeRequired': 'Doesn\'t Matter',
        'onCallRequirements': ['None', 'Occasional (once a month or less)', 'Regular (once a week or more)'],
        'usaGovPref': None,
        'searchQuery': '',
        'dateFetchedPastNDays': 121,
        'user': None,
        'searchModeSelectedCompany': None,
        'sortBy': 'default',
        'technologyKeywordsQuery': '',
        'requirementsKeywordsQuery': '',
        'companyPublicOrPrivate': 'all',
        'latestInvestmentAmount': None,
        'isNonProfit': 'all',
        'minYearFounded': None,
        'maxYearFounded': None
    }

    # not entirely sure how dateFetchedPastNDays
    # is derived, so use a manual mapping for now
    #
    # the upper values probably are not necessary
    # but wanted to match HiringCafe filters
    period_mapping = {
        # -1: -1,       # all time
        86400: 2,       # 24 hours
        259200: 4,      # 3 days
        604800: 14,     # 1 week
        1209600: 21,    # 2 weeks
        1814400: 29,    # 3 weeks
        2592000: 61,    # 1 month
        5184000: 91,    # 2 months
        7776000: 121,   # 3 months
        10368000: 151,  # 4 months
        12960000: 181,  # 5 months
        15552000: 211,  # 6 months
        31536000: 750,  # 1 year
        63072000: 1080, # 2 years
        94608000: 1440, # 3 years
    }

    def b64encode(self, data: dict) -> str:
        """Convert given dictionary to urlencoded base64."""
        state = urlencode({'s': json.dumps(data)})[2:].replace('+', ' ')
        return base64.b64encode(state.encode('utf-8')).decode('utf-8')

    def get_json(self, tag):
        if (pre := tag.find('pre')) is not None:
            return json.loads(pre.text.strip())
        return {}

    def get_search_url(self, endpoint: str, state: str, page: int = 0) -> str:
        params = {
            's': state,
            'size': self.JOBS_PER_PAGE,
            'page': page,
        }
        return f'https://hiring.cafe/api/search-jobs{endpoint}?{urlencode(params)}'

    def get_job_count(self, state: str) -> int:
        url = self.get_search_url('/get-total-count', state)
        tag = self.get(url)
        if not tag:
            logger.error('Unable to retrieve job count.')
            return 0
        
        try:
            return self.get_json(tag)['total']
        except Exception:
            logger.exception('Error parsing job count.')
            return 0

    def get_page_count(self, state: str) -> int:
        """Return number of pages to search.

        HiringCafe uses 0-index pagination.
        """
        count = self.get_job_count(state)
        if count == 0:
            return 0
        return (count // self.JOBS_PER_PAGE)

    def generate_state(self, search: Search, period: int | None = None) -> str:
        self.search_state['searchQuery'] = search.keywords
        if period is not None:
            # TODO: this should really be a separate
            # calculation but for now hijack LinkedIn
            # period calculation and manually clamp to
            # most appropriate mapping from dictionary
            if search.last_executed_at is None:
                period = 15552000
            key = min(self.period_mapping.keys(), key=lambda x: abs(x - period))
            self.search_state['dateFetchedPastNDays'] = self.period_mapping[key]
        return self.b64encode(self.search_state)

    def parse_job(self, result: dict):
        error: str | None = None
        job = {}

        try:
            job['company'] = result['v5_processed_job_data']['company_name']
            job['company_url'] = result['v5_processed_job_data']['company_website']
        except Exception:
            logger.exception('Error parsing company information')
            error = 'company'

        try:
            job['title'] = result['job_information']['title']
        except Exception:
            logger.exception('Error parsing job title')
            error = 'title'

        try:
            job['url'] = result['apply_url']
        except Exception:
            logger.exception('Error parsing job url')
            error = 'url'

        try:
            # TODO: at some point these locations
            # should be normalized with LinkedIn
            if result['v5_processed_job_data'].get('number_of_workplace_cities', 0) == 1:
                location = result['v5_processed_job_data']['workplace_cities'][0]
            elif result['v5_processed_job_data'].get('number_of_workplace_counties', 0) == 1:
                location = result['v5_processed_job_data']['workplace_counties'][0]
            elif result['v5_processed_job_data'].get('number_of_workplace_states', 0) == 1:
                location = result['v5_processed_job_data']['workplace_states'][0]
            elif result['v5_processed_job_data'].get('number_of_workplace_countries', 0) == 1:
                location = result['v5_processed_job_data']['workplace_countries'][0]
            elif result['v5_processed_job_data'].get('number_of_workplace_continents', 0) == 1:
                location = result['v5_processed_job_data']['workplace_continents'][0]
            else:
                location = None
            job['location'] = location
        except Exception:
            logger.exception('Unable to get location. Setting to None')
            job['location'] = None

        try:
            job['date_posted'] = str(datetime.fromtimestamp(result['v5_processed_job_data']['estimated_publish_date_millis'] / 1000.0))
        except Exception:
            logger.exception('Error parsing job post date')
            error = 'date_posted'

        job['date_found'] = str(timezone.now())

        # HiringCafe provides all the fields that
        # would usually be set on job population,
        # so include with initial job data

        try:
            job['description'] = result['job_information']['description'].strip()
        except Exception:
            logger.exception('Error parsing job description. Setting to empty string')
            job['description'] = ''

        job['raw_html'] = result

        if error is not None:
            return None
        return job

    def parse(self, search: Search, page=0, period: int | None = None) -> list[dict]:
        """Parse jobs."""
        jobs: list[dict] = []
        state = self.generate_state(search, period)
        
        url = self.get_search_url('', state, page=page)
        tag = self.get(url)
        if not tag:
            logger.warning('Response for %s is None', url)
            return jobs

        data = self.get_json(tag)
        if 'error' in data:
            raise Exception(data['error'])

        for result in data['results']:
            job = self.parse_job(result)
            if job is not None:
                jobs.append(job)
        return jobs
