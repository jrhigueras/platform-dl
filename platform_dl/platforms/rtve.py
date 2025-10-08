import base64
import requests
import urllib.parse
from typing import List

from . import Platform
from ..downloaders.axel import Axel
from ..models import Show, Season, Episode

pointer = 0


class RTVE(Platform[Axel]):
    base_api_url = "https://api.rtve.es/api"

    class PNG_RTVE_Data:
        # Borrowed from https://github.com/forestrf/Descargavideos - Thanks!
        @staticmethod
        def Img2ByteArray(imgDownloaded: str) -> list[int]:
            decoded = base64.b64decode(imgDownloaded)
            byteArray = [
                int(f"{ord(byte):08b}", 2)
                for byte in decoded.decode('latin1')
            ]
            return byteArray

        @staticmethod
        def readChunk(byteArray: list[int]) -> dict | None:
            global pointer

            e = RTVE.PNG_RTVE_Data.readInt(byteArray)
            if not e:
                return

            i = RTVE.PNG_RTVE_Data.readChars(byteArray, 4)
            if not i:
                return

            r = []
            if RTVE.PNG_RTVE_Data.read(byteArray, r, 0, e) != e:
                raise Exception("Out of bounds")

            pointer += 4
            return {
                'type': i,
                'data': r
            }

        @staticmethod
        def readInt(byteArray: list[int]) -> int:
            global pointer

            if pointer + 4 > len(byteArray):
                return False
            t0 = byteArray[pointer]
            t1 = byteArray[pointer + 1]
            t2 = byteArray[pointer + 2]
            t3 = byteArray[pointer + 3]
            pointer += 4
            return (t0 << 24) | (t1 << 16) | (t2 << 8) | t3

        @staticmethod
        def readChars(byteArray: list[int], t: int) -> str | None:
            global pointer

            if pointer + t > len(byteArray):
                return
            result = ''.join(chr(byteArray[pointer + i]) for i in range(t))
            pointer += t
            return result

        @staticmethod
        def read(byteArray: list[int], t: list[int], r: int, i: int) -> int:
            global pointer

            if pointer + i > len(byteArray):
                return False
            e = 0
            for e in range(i):
                n = byteArray[pointer]
                t.append(n)
                pointer += 1
            return e + 1

        @staticmethod
        def getSource(item: str) -> str:
            s = item.find("#")
            n = RTVE.PNG_RTVE_Data.getAlfabet(item[:s])
            r = item[s + 1:]
            return RTVE.PNG_RTVE_Data.getURL(r, n)

        @staticmethod
        def getAlfabet(t: str) -> str:
            r = ""
            e = 0
            n = 0
            for i in range(len(t)):
                if n == 0:
                    r += t[i]
                    e = (e + 1) % 4
                    n = e
                else:
                    n -= 1
            return r

        @staticmethod
        def getURL(texto: str, alfabeto: str) -> str:
            i = ""
            n = 0
            s = 3
            h = 1
            for e in range(len(texto)):
                if n == 0:
                    a = 10 * int(texto[e])
                    n = 1
                else:
                    if s == 0:
                        a += int(texto[e])
                        i += alfabeto[a]
                        s = (h + 3) % 4
                        n = 0
                        h += 1
                    else:
                        s -= 1
            return i

    @staticmethod
    def get_info_from_image_base(img: str) -> List[str] | None:
        if img != '':
            byteArray = RTVE.PNG_RTVE_Data.Img2ByteArray(img)

            global pointer
            pointer = 8  # Reinicia el puntero global para esta función
            encontrados = []

            while True:
                chunk = RTVE.PNG_RTVE_Data.readChunk(byteArray)
                if not chunk:
                    break

                if chunk['type'] == "tEXt":
                    data = chunk['data']
                    h = ''.join(
                        chr(data[o])
                        for o in range(len(data))
                        if data[o] != 0
                    )

                    if '%%' in h:
                        parts = h.split('#')
                        h = parts[0] + '#' + parts[1].split('%%')[1]

                    res = RTVE.PNG_RTVE_Data.getSource(h)
                    encontrados.append(res)

                if chunk['type'] == "IEND":
                    break

            if len(encontrados) > 0:
                return encontrados

    @staticmethod
    def get_info_from_image(video_id: str | int) -> List[str]:
        urls = [
            f"http://ztnr.rtve.es/ztnr/movil/thumbnail/rtveplayw/videos/{video_id}.png?q=v2",  # noqa: E501
            # f"http://www.rtve.es/ztnr/movil/thumbnail/default/videos/{video_id}.png",
        ]
        out = []
        for url in urls:
            r = requests.get(url)
            try:
                data = r.json()
                if data.get('error'):
                    return []
            except Exception:
                data = r.text
            img = data
            r = RTVE.get_info_from_image_base(img)
            if r and isinstance(r, list):
                [out.append(item) for item in r if item not in out]
        return out

    def _get_download_url(self, video_id: str) -> str:
        urls = self.get_info_from_image(video_id)
        best = urls[-1]
        parsed = urllib.parse.urlparse(best)
        # parsed = parsed._replace(query='')
        parsed = parsed._replace(netloc='rtve-mediavod-lote3.rtve.es')
        return parsed.geturl()

    def search(self, name: str) -> List[Show]:
        self.logger.info(f"Searching for {name}")
        url = f"{self.base_api_url}/search/programs?search={name}&page=1&size=10"  # noqa: E501
        r = self.session.get(url)
        return [
            Show(
                id=item['id'],
                title=item['title']
            )
            for item in r.json()['page']['items']
        ]

    def get_seasons(self, show: Show) -> List[Season]:
        url = f"{self.base_api_url}/programas/{show.id}/temporadas"
        r = self.session.get(url)
        data = r.json()
        seasons = [
            Season(
                id=item['id'],
                title=item['longTitle'],
                show=show
            )
            for item in data['page']['items']
        ]
        show.seasons = seasons
        return seasons

    def get_episodes(self, show: Show, season: Season) -> List[Episode]:
        if season.id and season.id != 0:
            url = f"{self.base_api_url}/programas/{show.id}/temporadas/{season.id}/videos"  # noqa: E501
        else:
            url = f"{self.base_api_url}/programas/{show.id}/videos"
        url += "?size=500"
        r = self.session.get(url)
        data = r.json()
        episodes = []
        i = 0
        for item in reversed(data['page']['items']):
            if item['type']['name'] == 'Completo':
                if self.is_excluded(item['title']):
                    continue
                number = item['episode']
                if number == 0:
                    i += 1
                    number = i

                episodes.append(
                    Episode(
                        id=item['id'],
                        title=item['title'],
                        description=item['description'],
                        url=self._get_download_url(item['id']),
                        number=number,
                        season=season
                    )
                )
        if season:
            season.episodes = episodes
        return episodes
