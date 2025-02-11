from setuptools import setup, find_packages

setup(
    name="stream2mediaserver",
    version="0.1.4",
    description="Prototype for locating TV series/anime streams",
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4',
        'm3u8',
        'py3createtorrent'
    ]
)