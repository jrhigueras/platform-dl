from setuptools import setup, find_packages

setup(
    name="platform-dl",
    version="0.0.1",
    description="A platform downloader tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Juan Ramón Higueras Pica",
    author_email="jrhigueras@gmail.com",
    url="https://github.com/jrhigueras/platform-dl",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "platform-dl=platform_dl.__main__:main",
        ],
    },
    python_requires=">=3.10",
    install_requires=[
        "requests",
        "yt-dlp",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
