import logging
import os
import pkgutil
import requests
from abc import ABC, abstractmethod
from argparse import Namespace
from multiprocessing.pool import Pool
from typing import List, Type, TypeVar, Generic, get_args

from ..models import Show, Season, Episode
from ..utils import file_exists
from ..downloaders import Downloader

T = TypeVar('T', bound=Downloader)


class Platform(ABC, Generic[T]):
    dry_run = False
    pool: Pool
    session: requests.Session
    output_file = "{episode.season.show.title} - S{episode.season.number:02}E{episode.number:02} - {episode.title}.{container}"  # noqa: E501
    container = "mp4"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"  # noqa: E501

    def __init__(self, args: Namespace):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing")
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        self.pool = Pool(processes=args.concurrency)
        self.dry_run = args.dry_run

        if args.username and args.password:
            try:
                ok = self.authenticate(args.username, args.password)
                if not ok:
                    self.logger.error("Authentication failed")
                    raise SystemExit(1)
            except NotImplementedError:
                self.logger.warning("Authentication not implemented")

    @property
    def downloader(self) -> Type[T]:
        return get_args(self.__orig_bases__[0])[0]  # type: ignore

    def authenticate(self, username: str, password: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def search(self, name: str) -> List[Show]:
        raise NotImplementedError

    @abstractmethod
    def get_seasons(self, show: Show) -> List[Season]:
        raise NotImplementedError

    @abstractmethod
    def get_episodes(self, show: Show, season: Season) -> List[Episode]:
        raise NotImplementedError

    def get_filename(self, episode: Episode) -> str:
        return self.output_file.format(episode=episode, container=self.container)  # noqa: E501

    def download(self, episodes: List[Episode]) -> None:
        for episode in episodes:
            self.logger.info(f"Downloading {self.get_filename(episode=episode)}")  # noqa: E501
            self.download_episode(episode)
        self.pool.close()
        self.pool.join()

    def download_episode(self, episode: Episode) -> None:
        if not episode.url:
            self.logger.warning(f"Episode {episode.title} has no URL")
            return
        filename = self.get_filename(episode=episode)  # noqa: E501
        if file_exists(filename):
            self.logger.warning(f"File {filename} already downloaded")
            return

        if self.dry_run:
            return

        downloader = self.downloader()

        self.pool.apply_async(
            downloader.run,
            kwds={
                'filename': filename,
                'url': episode.url
            },
            callback=lambda x: self.logger.info(f"Downloaded {filename}"),
            error_callback=lambda x: self.logger.error(f"Error downloading {filename}: {x}")  # noqa: E501
        )

    @staticmethod
    def get_platform(name: str) -> Type['Platform']:
        for _, module_name, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):  # noqa: E501
            module = __import__(f"{__name__}.{module_name}", fromlist=[''])
            for platform in module.__dict__.values():
                if isinstance(platform, type) and issubclass(platform, Platform) and platform != Platform:  # noqa: E501
                    if platform.__name__.lower() == name.lower():
                        return platform
        raise ValueError(f"Platform {name} not found")


class PaidSubscriptionError(Exception):
    pass
