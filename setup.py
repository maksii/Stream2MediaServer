from setuptools import setup, find_packages

setup(
    name="stream2mediaserver",
    version="0.1.2",
    description="Addon to facilitate locating and adding TV series/anime streams with standardized naming for Sonarr/Plex/Jellyfin integration.",
    url="https://github.com/maksii/stream2mediaserver",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'stream2mediaserver': ['data/*'],
    },
    entry_points={
        'console_scripts': [
            'stream2mediaserver=stream2mediaserver.main:main',
        ],
    },
    install_requires=[
        'requests',
        'beautifulsoup4',
        'm3u8'
    ]
)