from typing import List

from . import Platform, PaidSubscriptionError, UserRequiredError
from ..downloaders.ffmpeg import FFMPEG
from ..models import Show, Season, Episode


class A3Player(Platform[FFMPEG]):
    base_api_url = "https://api.atresplayer.com"
    container = "mkv"

    def authenticate(self, username: str, password: str) -> bool:
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*"
        }

        response = self.session.post(
            "https://account.atresplayer.com/auth/v1/login",
            headers=headers,
            data={
                "username": username,
                "password": password
            }
        )

        return response.status_code == 200

    def _get_download_url(self, video_id: str) -> str | None:
        r = self.session.get(f"{self.base_api_url}/player/v1/episode/{video_id}")  # noqa: E501
        data = r.json()
        if data.get('error'):
            if data['error'] == 'required_paid':
                raise PaidSubscriptionError("This episode requires a paid subscription")  # noqa: E501
            elif data['error'] == 'required_registered':
                raise UserRequiredError("This episode requires a registered user")  # noqa: E501

        for source in data.get('sources', []):
            if source['type'] == 'application/vnd.apple.mpegurl':
                return source['src']

    def search(self, show_name: str) -> List[Show]:
        self.logger.info(f"Searching for {show_name}")
        url = f"{self.base_api_url}/client/v1/row/search"
        params = {
            "entityType": "ATPFormat",
            "text": show_name,
            "size": 100,
            "page": 0
        }

        r = self.session.get(url, params=params)
        return [
            Show(
                id=item['contentId'],
                title=item['title']
            )
            for item in r.json()['itemRows']
        ]

    def get_seasons(self, show: Show) -> List[Season]:
        url = f"{self.base_api_url}/client/v1/page/format/{show.id}"
        r = self.session.get(url)
        data = r.json()
        seasons = [
            Season(
                id=item['link']['href'].split('seasonId=')[1],
                title=item['title'],
                show=show
            )
            for item in data['seasons']
        ]
        show.seasons = seasons
        return seasons

    def get_episodes(self, show: Show, season: Season) -> List[Episode]:
        url = f"{self.base_api_url}/client/v1/page/format/{show.id}?seasonId={season.id}"  # noqa: E501
        r = self.session.get(url)
        data = r.json()
        for row in data.get('rows', []):
            if row.get('type') == "EPISODE":
                url = row.get('href')
                break

        r = self.session.get(url, params={"size": 100})
        data = r.json()
        episodes = []
        for item in data['itemRows']:
            episode_id = item['contentId']
            title = item['title']
            r2 = self.session.get(f"{self.base_api_url}/client/v1/page/episode/{episode_id}")  # noqa: E501
            data2 = r2.json()
            try:
                download_url = self._get_download_url(episode_id)
            except PaidSubscriptionError:
                self.logger.warning(f"Episode {title} requires a paid subscription")  # noqa: E501
                continue
            except UserRequiredError:
                self.logger.warning(f"Episode {title} requires a registered user")  # noqa: E501
                continue
            episodes.append(
                Episode(
                    id=episode_id,
                    title=title,
                    description=data2['description'],
                    url=download_url,
                    number=data2['numberOfEpisode'],
                    season=season
                )
            )
        if season:
            season.episodes = episodes
        return episodes
