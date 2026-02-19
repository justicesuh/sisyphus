from sisyphus.searches.parsers.base import BaseParser
from sisyphus.searches.parsers.hiringcafe import HiringCafeParser
from sisyphus.searches.parsers.linkedin import LinkedInParser

PARSERS: dict[str, type[BaseParser]] = {
    HiringCafeParser.name: HiringCafeParser,
    LinkedInParser.name: LinkedInParser,
}
