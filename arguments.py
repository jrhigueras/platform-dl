import argparse

from .utils import parse_episode_mask


def init() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Downloads stuff from online platforms"
    )
    parser.add_argument(
        '--platform',
        type=str,
        help="The platform to download from.",
        required=True
    )
    parser.add_argument(
        'query',
        type=str,
        nargs=1,
        help="The content you would like to search.",
    )
    parser.add_argument(
        '--username',
        type=str,
        help="The username to log into the platform."
    )
    parser.add_argument(
        '--password',
        type=str,
        help="The password to log into the platform."
    )
    parser.add_argument(
        '-e', '--episodes',
        type=str,
        help="The episode mask you would like to download. Examples: 1-5 | 1,3,7 | >5 | <12 | 7"  # noqa: E501
    )
    parser.add_argument(
        '-s', '--season',
        type=int,
        help="Specificy which season to download.",
        default=0
    )
    parser.add_argument(
        '-c', '--concurrency',
        type=int,
        help="Number of concurrent downloads.",
        default=2
    )
    parser.add_argument(
        '--dry-run',
        action="store_true",
        help="It will NOT download anything, just show what will be downloaded."  # noqa: E501
    )
    parser.add_argument(
        '--include',
        type=str,
        help="Include regex for the episode title.",
    )
    parser.add_argument(
        '--exclude',
        type=str,
        help="Exclude regex for the episode title.",
    )
    args = parser.parse_args()
    args.query = " ".join(args.query)

    if args.episodes:
        parse_episode_mask(args.episodes)

    return args
