import logging
from . import arguments
from .platforms import Platform
from .models import Season
from .utils import select_show, select_season, select_episodes

logging.basicConfig(level=logging.INFO)


def main():
    args = arguments.init()
    platform = Platform.get_platform(args.platform)(args)

    shows = platform.search(args.query)
    if not shows:
        platform.logger.error("No shows found")
        exit(1)
    show = select_show(shows)

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
