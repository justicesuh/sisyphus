from sisyphus.searches.parsers.base import BaseParser
from sisyphus.searches.parsers.linkedin import LinkedInParser

PARSERS: dict[str, type[BaseParser]] = {
    LinkedInParser.name: LinkedInParser,
}
