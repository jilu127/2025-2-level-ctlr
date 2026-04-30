"""
Crawler implementation.
"""

# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable, unused-argument
import datetime
import json
import pathlib

import requests
from bs4 import BeautifulSoup, Tag

from core_utils.article.article import Article
from core_utils.config_dto import ConfigDTO
from core_utils.constants import CRAWLER_CONFIG_PATH, ASSETS_PATH
#from core_utils.article.io import to_raw, to_meta

import shutil


class IncorrectSeedURLError(Exception):
    """Raised when seed URL does not match standard pattern 'https?://(www.)?'."""
    pass


class NumberOfArticlesOutOfRangeError(Exception):
    """Raised when total number of articles is out of range from 1 to 150."""
    pass


class IncorrectNumberOfArticlesError(Exception):
    """Raised when total number of articles to parse is not integer or less than 0."""
    pass


class IncorrectHeadersError(Exception):
    """Raised when headers are not in a form of dictionary."""
    pass


class IncorrectEncodingError(Exception):
    """Raised when encoding is not specified as a string."""
    pass


class IncorrectTimeoutError(Exception):
    """Raised when timeout value is not a positive integer less than 60."""
    pass


class IncorrectVerifyError(Exception):
    """Raised when verify certificate value is not boolean."""
    pass


class IncorrectHeadlessModeError(Exception):
    """Raised when headless mode value is not boolean."""
    pass


class Config:
    """
    Class for unpacking and validating configurations.
    """

    def __init__(self, path_to_config: pathlib.Path) -> None:
        """
        Initialize an instance of the Config class.

        Args:
            path_to_config (pathlib.Path): Path to configuration.
        """
        self.path_to_config = path_to_config
        self._config_dto = self._extract_config_content()
        self._validate_config_content()
        

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as file:
            return ConfigDTO(**json.load(file))

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        cfg = self._config_dto
        if not cfg.seed_urls or not all(u.startswith(('http://', 'https://')) for u in cfg.seed_urls):
            raise IncorrectSeedURLError()
        if not isinstance(cfg.total_articles, int) or not (1 <= cfg.total_articles <= 150):
            raise NumberOfArticlesOutOfRangeError()
        if not isinstance(cfg.headers, dict):
            raise IncorrectHeadersError()
        if not isinstance(cfg.encoding, str):
            raise IncorrectEncodingError()
        if not isinstance(cfg.timeout, int) or not (1 <= cfg.timeout <= 59):
            raise IncorrectTimeoutError()
        if not isinstance(cfg.should_verify_certificate, bool):
            raise IncorrectVerifyError()
        if not isinstance(cfg.headless_mode, bool):
            raise IncorrectHeadlessModeError()

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls.

        Returns:
            list[str]: Seed urls
        """
        return self._config_dto.seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape.

        Returns:
            int: Total number of articles to scrape
        """
        return self._config_dto.total_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting.

        Returns:
            dict[str, str]: Headers
        """
        return self._config_dto.headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing.

        Returns:
            str: Encoding
        """
        return self._config_dto.encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response.

        Returns:
            int: Number of seconds to wait for response
        """
        return self._config_dto.timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate.

        Returns:
            bool: Whether to verify certificate or not
        """
        return self._config_dto.should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode.

        Returns:
            bool: Whether to use headless mode or not
        """
        return self._config_dto.headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Deliver a response from a request with given configuration.

    Args:
        url (str): Site url
        config (Config): Configuration

    Returns:
        requests.models.Response: A response from a request
    """
    response = requests.get(
        url,
        headers=config.get_headers(),
        timeout=config.get_timeout(),
        verify=config.get_verify_certificate()
    )
    response.encoding = config.get_encoding()
    return response


class Crawler:
    """
    Crawler implementation.
    """

    #: Url pattern
    url_pattern: re.Pattern | str

    def __init__(self, config: Config) -> None:
        """
        Initialize an instance of the Crawler class.

        Args:
            config (Config): Configuration
        """
        self.config = config
        self.urls = []

    def _extract_url(self, article_bs: Tag) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.Tag): Tag instance

        Returns:
            str: Url from HTML
        """
        href = article_bs.get('href')
        if href.startswith('/'):
            return 'https://proza.ru' + href
        return href

    def find_articles(self) -> None:
        """
        Find articles.
        """
        full_url = self._extract_url(link)
        if full_url not in self.urls:
            self.urls.append(full_url)
        seed_urls = self.config.get_seed_urls()
        needed_count = self.config.get_num_articles()
        for seed_url in seed_urls:
            if len(self.urls) >= needed_count:
                break
            response = make_request(seed_url, self.config)
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, 'lxml')
            article_links = soup.find_all('a', class_='poemlink')
            for link in article_links:
                if len(self.urls) >= needed_count:
                    break
                full_url = self._extract_url(link)
                if full_url not in self.urls:
                    self.urls.append(full_url)

    def get_search_urls(self) -> list:
        """
        Get seed_urls param.

        Returns:
            list: seed_urls param
        """
        return self.config.get_seed_urls()


# 10


class CrawlerRecursive(Crawler):
    """
    Recursive implementation.

    Get one URL of the title page and find requested number of articles recursively.
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize an instance of the CrawlerRecursive class.

        Args:
            config (Config): Configuration
        """

    def find_articles(self) -> None:
        """
        Find number of article urls requested.
        """


# 4, 6, 8, 10


class HTMLParser:
    """
    HTMLParser implementation.
    """

    def __init__(self, full_url: str, article_id: int, config: Config) -> None:
        """
        Initialize an instance of the HTMLParser class.

        Args:
            full_url (str): Site url
            article_id (int): Article id
            config (Config): Configuration
        """
        self.full_url = full_url
        self.article_id = article_id
        self.config = config
        self.article = Article(full_url, article_id)
        

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """

    def parse(self) -> Article | bool:
        """
        Parse each article.

        Returns:
            Article | bool: Article instance, False in case of request error
        """
        response = make_request(self.full_url, self.config)
        soup = BeautifulSoup(response.text, 'lxml')
        self._fill_article_with_text(soup)
        self._fill_article_with_meta_information(soup)
        return self.article


def prepare_environment(base_path: pathlib.Path | str) -> None:
    """
    Create ASSETS_PATH folder if no created and remove existing folder.

    Args:
        base_path (pathlib.Path | str): Path where articles stores
    """
    path = pathlib.Path(base_path)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    Entrypoint for scraper module.
    """


if __name__ == "__main__":
    main()
