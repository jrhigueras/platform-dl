from . import Downloader


class Axel(Downloader):
    command = ["axel", "-a", "-n", "10", "-o", "{filename}", "{url}"]
