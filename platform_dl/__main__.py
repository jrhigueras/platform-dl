import logging
from . import arguments
from .platforms import Platform
from .models import Season, Show
from .utils import select_show, select_season, select_episodes
from typing import Dict, List

logging.basicConfig(level=logging.INFO)


def main():
    args = arguments.init()
    shows_map: Dict[Platform, List[Show]] = {}
    platform: Platform | None = None

    if args.platform:
        platform = Platform.get_platform(args.platform)(args)
        shows = platform.search(args.query)
        if not shows:
            platform.logger.error("No shows found")
            exit(1)
    else:
        logging.info("No platform specified, searching all platforms")
        shows = []
        for platform_cls in Platform.get_all_platforms():
            try:
                p = platform_cls(args)
                s = p.search(args.query)
                shows_map[p] = s
                shows.extend(s)
            except Exception as e:
                logging.error(f"Error searching in {platform_cls.__name__}: {e}")

    show = select_show(shows)
    if not platform and shows_map:
        platform = next(p for p, s in shows_map.items() if show in s)
        logging.info(f"Selected platform: {platform}")
        if platform.authenticate != Platform.authenticate:
            logging.info("You may need to authenticate to download episodes")

    assert platform is not None, "Platform could not be determined"

    seasons = platform.get_seasons(show)
    if seasons:
        season = select_season(show)
    else:
        season = Season(id=0, title="Unknown", show=show)

    episodes = platform.get_episodes(show, season)
    if not episodes:
        platform.logger.error("No episodes found")
        exit(1)

    episodes = select_episodes(episodes)
    platform.download(episodes)


if __name__ == "__main__":
    main()
