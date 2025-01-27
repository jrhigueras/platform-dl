from . import Downloader


class FFMPEG(Downloader):
    command = ["ffmpeg", "-i", "{url}", "-c", "copy", "{filename}", "-y"]
