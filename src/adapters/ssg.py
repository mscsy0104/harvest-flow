from __future__ import annotations

from harvest_flow_core.interfaces import SSGPublisher
from harvest_flow.utils import publish_content, unpublish_content


class GitHubSSGAdapter(SSGPublisher):
    """GitHub/Quartz-backed SSG publisher."""

    def publish_content(self, file_name: str) -> bool:
        return publish_content(file_name)

    def unpublish_content(self, file_name: str) -> bool:
        return unpublish_content(file_name)

