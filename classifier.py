"""Wojak classifier: walk the wojak_index.json tree with TypeSafe jev.

jev Choice questions cap at 255 options and the collection is 640+ images,
so classification is a tree walk: one Choice per node, image leaf ends it.
"""

import json
import os
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

ROOT = Path(__file__).parent
IMAGE_DIR = ROOT / "wojack_source_images"
INDEX = ROOT / "wojak_index.json"

INSTRUCTIONS = ("The state is a message or situation someone wants to react "
                "to. Pick the option whose wojak meme would be the best "
                "reply to it.")


def load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


class WojakClassifier:
    def __init__(self, index_path: Path | None = None):
        load_env()
        # WOJAK_INDEX selects the index; defaults to the committed SFW set.
        # Full-library deployments set WOJAK_INDEX=wojak_index.full.json.
        index_path = index_path or ROOT / os.environ.get(
            "WOJAK_INDEX", "wojak_index.json")
        self.tree = json.loads(index_path.read_text())
        self.client = TypeSafeClient()  # reads TYPESAFE_API_KEY
        self._summaries: dict[int, str] = {}  # id(group node) -> criteria text

    def _summary(self, node: dict) -> str:
        """Criteria text for a group node: name plus sample member wojaks."""
        if id(node) not in self._summaries:
            names = [l["name"] for l in self._leaves(node)]
            sample = ", ".join(names[:6])
            more = f" and {len(names) - 6} more" if len(names) > 6 else ""
            self._summaries[id(node)] = (
                f'A category of wojaks called "{node["name"]}", containing '
                f"wojaks such as: {sample}{more}")
        return self._summaries[id(node)]

    def _leaves(self, node: dict):
        if "path" in node:
            yield node
        else:
            for c in node["children"]:
                yield from self._leaves(c)

    def classify(self, prompt: str) -> tuple[dict, list[tuple[str, float]]]:
        """Return (image leaf, walk trail of (node name, confidence))."""
        node = self.tree
        trail: list[tuple[str, float]] = []
        while "children" in node:
            criteria = {}
            for child in node["children"]:
                if "path" in child:
                    criteria[child["name"]] = child.get("description")
                else:
                    criteria[child["name"]] = self._summary(child)
            resp = self.client.system_one(
                state=prompt,
                questions={"pick": Choice(instructions=INSTRUCTIONS,
                                          criteria=criteria)},
            )
            answer = resp.answers["pick"]
            match = next((c for c in node["children"]
                          if c["name"] == answer.choice), None)
            if match is None:
                raise RuntimeError(
                    f"jev picked unknown option {answer.choice!r} at "
                    f"{node['name']!r}")
            trail.append((match["name"], answer.confidence))
            node = match
        return node, trail

    def resolve(self, leaf: dict) -> Path:
        return IMAGE_DIR / leaf["path"]
