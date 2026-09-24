"""Cut the committed SFW index (wojak_index.json) from the full library index.

The repo ships a curated set of the 50 funniest SFW wojaks. The full library
stays out of git; deployments regenerate it with build_index.py and select it
via WOJAK_INDEX=wojak_index.full.json.

Reads wojak_index.full.json, keeps only the paths in KEEP, prunes empty
groups, writes wojak_index.json. Fails loudly on any missing path so renames
in the source collection surface here.

Usage: python3 curate_index.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
FULL = ROOT / "wojak_index.full.json"
OUT = ROOT / "wojak_index.json"

KEEP = [
    # regular wojaks
    "regular wojaks/Wojak.png",
    "regular wojaks/ComputerWojak.webp",
    "regular wojaks/ClownWojak.png",
    "regular wojaks/DrivingWojak.png",
    "regular wojaks/BlanketWojak.png",
    "regular wojaks/CoveringFaceWojak.png",
    "regular wojaks/HappyCryingWojak.png",
    "regular wojaks/ShruggingWojak.png",
    "regular wojaks/WojakChilling.png",
    "regular wojaks/FeeliumWojak.png",
    "regular wojaks/FascadeWojak.png",
    "regular wojaks/WojakGroupHug.png",
    # soyjaks
    "soyjaks/Soyjak.png",
    "soyjaks/Soyjak2.png",
    "soyjaks/SoyjakPointing.png",
    "soyjaks/SoyjakGuzzling.png",
    "soyjaks/SoyjakCrying.png",
    "soyjaks/GroupOfSoyjaks.png",
    # Chads
    "Chads/Chad.png",
    "Chads/NordicChadFrontView.png",
    "Chads/BoomerChad.png",
    "Chads/John Maynard Keynes.png",
    # doomers
    "doomers/doomer.png",
    "doomers/WojakPreDoom.png",
    "doomers/DoomerStage6.png",
    "doomers/DoomerGaming.png",
    "doomers/19CenturyDoomer.png",
    # rage wojaks
    "rage wojaks/RageRed.png",
    "rage wojaks/RageCrying.png",
    "rage wojaks/RageBrain2.png",
    "rage wojaks/RageCamel.png",
    # brainiaks
    "brainiaks/brainchair.png",
    "brainiaks/BrainCube.png",
    "brainiaks/wojak-big-brain-universe.png",
    # brainlets
    "brainlets/FalseBrainiac.png",
    "brainlets/MicrowaveBrainlet.png",
    "brainlets/LogBrainlet.png",
    "brainlets/WindUpBrainlet.png",
    "brainlets/HanginBrainlet.png",
    # NPCs
    "NPCs/NPC.PNG",
    "NPCs/TwitterVerifiedNPC.png",
    "NPCs/ShowerNPC.png",
    "NPCs/ComputerNPC2.png",
    # mask wojaks
    "mask wojaks/wojak-happy-mask.png",
    "mask wojaks/TiredMasked.png",
    "mask wojaks/EvilMasked2.png",
    # more characters
    "more characters/grug/ChadGrug.png",
    "more characters/boomers/ComputerBoomer.png",
    "more characters/boomers/LawnBoomer.PNG",
    "more characters/zoomers/ZoomerSmug.png",
]


def prune(node: dict, keep: set) -> dict | None:
    if "path" in node:
        return node if node["path"] in keep else None
    children = [c for c in (prune(c, keep) for c in node["children"]) if c]
    if not children:
        return None
    return {"name": node["name"], "children": children}


def main() -> None:
    tree = json.loads(FULL.read_text())
    keep = set(KEEP)
    pruned = prune(tree, keep)

    found = set()

    def collect(n):
        if "path" in n:
            found.add(n["path"])
        else:
            for c in n["children"]:
                collect(c)
    collect(pruned)

    missing = keep - found
    if missing:
        raise SystemExit(f"KEEP paths not in full index: {sorted(missing)}")

    pruned["name"] = "wojaks"
    OUT.write_text(json.dumps(pruned, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.name}: {len(found)} wojaks")


if __name__ == "__main__":
    main()
