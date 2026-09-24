# wojak-as-a-service

A Slack bot that replies to any prompt with the most applicable wojak, chosen
by a classifier. `/wojak my deploy just broke production` gets you a sobbing
pink wojak in about a quarter of a second.

An R&D toy from BitStorm Technologies about a serious idea: small,
structured decision models (classifiers) can do jobs we'd normally reach for
a chatbot to do, faster, cheaper, and with output your code can actually use.

## The trick

LLM-style "pick a meme" would mean generating text and parsing it. Instead,
every decision here is a typed question answered by
[jev](https://docs.typesafe.ai), a classifier that returns a probability
distribution over options you define.

Two problems had to be solved:

**1. Classifiers can't look at images.** So a vision model
([ember-1](https://app.fireworks.ai/models/fireworks/ember-1) via Fireworks)
writes a one-sentence description of each wojak first. The classifier never
sees pixels; it picks on meaning. Descriptions are generated once and cached
in the index (`build_index.py`, incremental on re-runs).

**2. Choice questions cap at 255 options, and there are 640+ wojaks.** So the
index is a tree (the folder taxonomy of the collection), and classification
is a walk: one Choice question per node, an image leaf ends it. 2 to 3 API
calls per prompt, each ~70-180 ms, which is where the KPI in every response
comes from: `time to wojak'd`. The tree-walk design exists because of the
255-option cap, but it has the standard hierarchical-classifier trade-off: a
wrong category pick is unrecoverable downstream.

```mermaid
flowchart LR
    A["/wojak prompt"] --> B["jev Choice:<br/>which category?"]
    B --> C["jev Choice:<br/>which wojak?"]
    C --> D["upload image<br/>+ time to wojak'd"]

## How it's classified

[jev](https://en.wikipedia.org/wiki/Jev_(AI_model)) is not an LLM: it
generates no text. Given a block of state (string or JSON) and typed
questions, it returns structured answers with probability estimates, trained
with RLCD (reinforcement learning for calibrated decisions), which optimizes
probabilities against outcomes rather than human preference. In principle
that makes its confidence scores calibrated; in practice, verify against
your own traffic before building thresholds on them.

What a 15-prompt live probe of this bot showed:

- **Picks are stable, confidences are not.** The same prompt classified 5
  times gave the same wojak all 5 times, with confidence wobbling plus or
  minus 0.1 between calls.
- **Most picks are soft.** Typical confidence was 0.2-0.5; jev is usually
  choosing among near-ties, so small description changes can flip outputs.
- **Errors happen at the root.** A wrong category pick (e.g. "waking up
  before the alarm" routed to Chads) cannot be fixed at the leaf level.

Every classification is traced to Logfire: each node question is a span
carrying the full state, instructions, criteria, chosen option, and
confidence, so picks are auditable after the fact.

## Run it

1. Create a Slack app from `slack_app_manifest.json` at
   https://api.slack.com/apps and install it to your workspace.
2. `cp .env.example .env` and fill in the keys.
3. `uv run python bot.py` (Socket Mode, no public URL needed), or
   `docker compose up -d --build`.

Then `/wojak anything at all` in Slack.

## The image set

The repo ships a curated set of the 50 funniest SFW wojaks
(`wojak_index.json` + the images), cut from a 642-image community collection
(see `wojack_source_images/original_forward.txt` for the original credits).
To use your own collection: drop images into `wojack_source_images/`, run
`python3 build_index.py` (writes `wojak_index.full.json`, describing any new
images via ember-1), and set `WOJAK_INDEX=wojak_index.full.json`.
`curate_index.py` shows how the SFW set was filtered from the full index.

## Layout

- `bot.py` - Slack app: `/wojak` handler, image upload, KPI
- `classifier.py` - the tree walk over jev Choice questions
- `build_index.py` - tree indexer + ember-1 description pipeline
- `curate_index.py` - the SFW 50 selection
