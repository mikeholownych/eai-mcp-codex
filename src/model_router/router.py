"""Model selection and routing logic based on configurable rules."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Pattern, Tuple

import yaml

from .config import settings
from .models import ModelRequest, ModelResponse


class RoutingTable:
    """In-memory routing table compiled from YAML rules."""

    def __init__(self, rules: Iterable[Tuple[str, str]]) -> None:
        self.rules: List[Tuple[Pattern[str], str]] = [
            (re.compile(pattern), model) for pattern, model in rules
        ]

    def select(self, text: str) -> str:
        """Return the first matching model for the given text."""
        for pattern, model in self.rules:
            if pattern.search(text):
                return model
        return "haiku"


def _load_rules(file_path: str) -> RoutingTable:
    if not Path(file_path).exists():
        return RoutingTable([(r".*", "haiku")])

    data = yaml.safe_load(Path(file_path).read_text())
    rules = [
        (rule.get("match", ".*"), rule["model"])
        for rule in data.get("rules", [])
        if "model" in rule
    ]
    return RoutingTable(rules)


_table = _load_rules(settings.rules_file)


def route(req: ModelRequest) -> ModelResponse:
    """Select a target model using routing rules."""
    model = _table.select(req.text)
    return ModelResponse(result=f"{model}:{req.text}")
