import urllib.parse
from typing import Any, Dict, List

from . import Platform
from ..downloaders.ytdlp import YTDLP
from ..models import Show, Season, Episode


class MiTele(Platform[YTDLP]):
    base_api_url = "https://mab.mediaset.es/1.0.0/get?oid=bitban&eid="
    container = "mp4"

    def _get_download_url(self, video_url: str) -> str:
        return "https://www.mitele.es" + video_url

    def search(self, show_name: str) -> List[Show]:
        self.logger.info(f"Searching for {show_name}")
        payload = f"/search/mtweb?url=www.mitele.es&text={show_name}"  # noqa: E501
        url = self.base_api_url + urllib.parse.quote(payload)

        r = self.session.get(url)
        return [
            Show(
                id=item['id'],
                title=item['title'],
                url=item['image']['href']
            )
            for item in r.json()['data']
        ]

    def get_seasons(self, show: Show) -> List[Season]:
        assert show.url, "Show URL is required"
        payload = "/container/mtweb?url=https://www.mitele.es" + show.url
        url = self.base_api_url + urllib.parse.quote(payload)
        r = self.session.get(url)
        if not r.ok:
            self.logger.error(r.text)
            exit(1)
        data = r.json()

        contents: List[Dict[str, Any]] = []

        for tab in data['tabs']:
            if tab['type'] == 'navigation':
                contents.extend(tab['contents'])
            else:
                contents.append(tab)

        if not contents:
            raise ValueError("No navigation tab found")

        seasons = [
            Season(
                id=item['id'],
                title=item['title'],
                show=show,
                url=item['link']['href']
            )
            for item in contents
        ]
        show.seasons = seasons
        return seasons

    def get_episodes(self, show: Show, season: Season) -> List[Episode]:
        assert season.url, "Season URL is required"
        if isinstance(season.id, str) and '.' not in season.id:
            season.id = season.id + ".0"
        payload = "/tabs/mtweb?url=https://www.mitele.es" + season.url
        payload += "&tabId=" + str(season.id)
        url = self.base_api_url + urllib.parse.quote(payload)
        r = self.session.get(url)
        data = r.json()

        contents = []

        for content in data['contents']:
            if content.get('children'):
                contents.extend(content['children'])
            else:
                contents.append(content)

        if not contents:
            raise ValueError("No children found")

        episodes = [
            Episode(
                id=item['id'],
                title=item['title'],
                description=item['info']['synopsis'],
                url=self._get_download_url(item['link']['href']),
                number=item['info']['episode_number'],
                season=season
            )
            for item in contents
            if not self.is_excluded(item['title'])
        ]

        if season:
            season.episodes = episodes
        return episodes
