import os
from typing import List

from .models import Show, Season, Episode


def parse_episode_mask(mask: str) -> List[int] | range:
    if '-' in mask:
        start, stop = mask.split('-')
        out = range(int(start), int(stop))
    elif ',' in mask:
        out = [int(x) for x in mask.split(',') if x]
    elif '<' in mask:
        stop = int(mask[1:])
        out = range(stop)
    elif '>' in mask:
        start = int(mask[1:]) + 1
        out = range(start, 2 << 30)
    elif 'a' in mask:
        out = range(1, 2 << 30)
    elif 'q' in mask:
        exit(0)
    else:
        out = [int(mask)]

    return out


def file_exists(filename: str) -> bool:
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        if os.path.exists(filename + ".st"):
            return False
        return True
    return False


def select_show(shows: List[Show]) -> Show:
    if len(shows) == 0:
        raise ValueError("No shows found")

    for i in range(len(shows)):
        print(f"{i+1} - {shows[i].title}")
    show = input("Select the show: ")

    try:
        return shows[int(show)-1]
    except (ValueError, IndexError):
        exit(0)


def select_season(show: Show) -> Season:
    if not show.seasons:
        raise ValueError("No seasons found")

    show.seasons.sort(key=lambda x: x.number)

    for season in show.seasons:
        print(f"{season.number} - {season.title}")
    season = input("Select the season: ")

    try:
        return show.seasons[int(season)]
    except (ValueError, IndexError):
        exit(0)


def select_episodes(episodes: List[Episode]) -> List[Episode]:
    if len(episodes) == 0:
        raise ValueError("No episodes found")

    episodes.sort(key=lambda x: x.number)

    for episode in episodes:
        print(f"{episode.number} - {episode.title}")
    print("\na - all episodes")

    selected = parse_episode_mask(input("Select the episodes: "))

    try:
        return [x for x in episodes if x.number in selected]
    except (ValueError, IndexError):
        exit(0)
