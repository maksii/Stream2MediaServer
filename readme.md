# Stream2MediaServer

Development prototype for locating TV series/anime streams.

## Installation

```bash
pip install -e .
```

## Usage

```python
from stream2mediaserver import MainLogic
from stream2mediaserver.config import config

# Initialize
logic = MainLogic()

# Search
results = await logic.search("your search query")

# Get details
for result in results:
    series = await logic.process_item(result)
    print(f"Found: {series.title}")
```

## Providers
- Animeon
- Anitube
- UAFlix
- UAKino

