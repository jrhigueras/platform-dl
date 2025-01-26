from . import Downloader


class YTDLP(Downloader):
    command = ["yt-dlp", "-o", "{filename}", "--embed-subs", "{url}"]
