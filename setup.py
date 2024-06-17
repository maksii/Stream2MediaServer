from setuptools import setup, find_packages

setup(
    name="stream2MediaServer",
    version="0.0.4",
    description="Addon to facilitate locating and adding TV series/anime streams with standardized naming for Sonarr/Plex/Jellyfin integration.",
    url="https://github.com/maksii/stream2MediaServer",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'stream2MediaServer': ['data/*'],
    },
    entry_points={
        'console_scripts': [
            'stream2MediaServer=stream2MediaServer.main:main',
        ],
    },
    install_requires=[
        'requests',
        'beautifulsoup4',
        'm3u8'
    ]
)