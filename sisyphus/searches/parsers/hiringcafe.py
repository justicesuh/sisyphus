import base64
import logging
import json
from typing import ClassVar
from urllib.parse import urlencode

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
                'address_components': [
                    {
                        'long_name': 'United States',
                        'short_name': 'US',
                        'types': ['country']
                    }
                ],
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

    def b64encode(self, data: dict) -> str:
        state = urlencode({'s': json.dumps(data)})[2:].replace('+', ' ')
        return base64.b64encode(state.encode('utf-8')).decode('utf-8')

    def get_json(self, tag):
        if (pre := tag.find('pre')) is not None:
            return json.loads(pre.text.strip())
        return {}

    def get_job_count(self):
        tag = self.get('https://hiring.cafe/api/search-jobs/get-total-count')
        return self.get_json(tag)

    def parse(self):
        return self.b64encode(self.search_state)