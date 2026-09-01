"""In-memory registries for sources and viewers."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class StreamSource:
    source_id: str
    name: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StreamRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, StreamSource] = {}

    def register(self, source: StreamSource) -> None:
        self._sources[source.source_id] = source

    def unregister(self, source_id: str) -> None:
        self._sources.pop(source_id, None)

    def list_sources(self) -> list[StreamSource]:
        return list(self._sources.values())
