"""Wojak-as-a-service Slack bot.

/wojak <prompt> walks the wojak index with jev and posts the best-fit wojak
image to the channel, with a "time to wojak'd" KPI (command receipt to pick).

Runs on Socket Mode: no public URL needed. Tokens from .env:
  SLACK_BOT_TOKEN (xoxb-..., from Install App)
  SLACK_APP_TOKEN (xapp-..., from Basic Information)

Usage: uv run python bot.py
"""

import logging
import os
import time

import logfire
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from classifier import WojakClassifier, load_env

load_env()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("wojak-bot")
logfire.configure(service_name="wojak-bot")

app = App(token=os.environ["SLACK_BOT_TOKEN"])
classifier = WojakClassifier()


@app.command("/wojak")
def handle_wojak(ack, command, client):
    t0 = time.monotonic()
    prompt = command.get("text", "").strip()
    if not prompt:
        ack("Usage: /wojak <situation or message>")
        return
    ack(f"finding the wojak for: _{prompt}_")

    with logfire.span("handle /wojak", prompt=prompt,
                      user=command["user_id"],
                      channel=command["channel_id"]) as span:
        try:
            leaf, trail = classifier.classify(prompt)
            elapsed = time.monotonic() - t0
            client.files_upload_v2(
                channel=command["channel_id"],
                file=str(classifier.resolve(leaf)),
                title=leaf["name"],
                initial_comment=(
                    f"*wojak'd* <@{command['user_id']}> for _{prompt}_\n"
                    f"*{leaf['name']}*: {leaf.get('description', '')}\n"
                    f"time to wojak'd: *{elapsed:.1f}s*"),
            )
            span.set_attribute("leaf", leaf["name"])
            span.set_attribute("elapsed_s", round(elapsed, 3))
            log.info("wojak'd %r -> %s in %.1fs via %s", prompt, leaf["path"],
                     elapsed, " > ".join(name for name, _ in trail))
        except Exception as e:
            log.exception("wojak failed for %r", prompt)
            logfire.exception("wojak failed", prompt=prompt)
            client.chat_postEphemeral(
                channel=command["channel_id"],
                user=command["user_id"],
                text=f"couldn't wojak that: {e}")


if __name__ == "__main__":
    log.info("wojak bot starting (socket mode)")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
