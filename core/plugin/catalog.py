from __future__ import annotations

from typing import Callable, Dict

from core.plugin.sdk import Plugin
from plugins.document_plugin import DocumentPlugin
from plugins.presentation_plugin import PresentationPlugin


def _doc_factory() -> Plugin:
    return DocumentPlugin()


def _presentation_factory() -> Plugin:
    return PresentationPlugin()


PLUGIN_CATALOG: Dict[str, Callable[[], Plugin]] = {
    "document.plugin.v1": _doc_factory,
    "presentation.plugin.v1": _presentation_factory,
}


def available_plugins() -> list[str]:
    return sorted(PLUGIN_CATALOG.keys())
