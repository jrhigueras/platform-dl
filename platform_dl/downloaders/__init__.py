import subprocess
from abc import ABC
from typing import List


class Downloader(ABC):
    command: List[str]

    def run(self, url: str, filename: str) -> subprocess.CompletedProcess:
        command = self.command.copy()
        for i, part in enumerate(command):
            if part.startswith("{") and part.endswith("}"):
                part = part.format(url=url, filename=filename)
                command[i] = part

        return subprocess.run(
            tuple(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True
        )
