from pathlib import Path

from setuptools import find_packages, setup


def read_version() -> str:
    init_path = Path(__file__).parent / "stream2mediaserver" / "__init__.py"
    for line in init_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Unable to determine package version.")


setup(
    name="stream2mediaserver",
    version=read_version(),
    description="Prototype for locating TV series/anime streams",
    packages=find_packages(),
    install_requires=["requests", "beautifulsoup4", "m3u8", "py3createtorrent"],
)
