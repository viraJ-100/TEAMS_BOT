# bot.py
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from parser import parse_install_command
from workflow import start_installation
from db_catalog import fetch_app_catalog
from cards import build_catalog_activity

class MyBot(ActivityHandler):

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        # Welcome + show catalog cards from MySQL
        apps = fetch_app_catalog(limit=10)
        if not apps:
            await turn_context.send_activity("👋 Welcome! No apps are configured yet. Ask an admin to add some to the catalog.")
            return

        await turn_context.send_activity("👋 Welcome! Pick an app below to install:")
        await turn_context.send_activity(build_catalog_activity(apps))

    async def on_message_activity(self, turn_context: TurnContext):
        # 1) Handle Adaptive Card submit (Action.Submit sends payload in activity.value)
        payload = turn_context.activity.value or {}
        if isinstance(payload, dict) and payload.get("intent") == "install_app":
            app = payload.get("app")
            version = payload.get("version") or "latest"
            user_id = str(turn_context.activity.from_property.id)

            await turn_context.send_activity(f"⏳ Starting installation of {app} {version}...")
            await start_installation(user_id, app, version, turn_context)
            return

        # 2) Fallback to text parsing (typed commands)
        user_input = (turn_context.activity.text or "").strip()
        user_id = str(turn_context.activity.from_property.id)

        # quick command to re-show catalog
        if user_input.lower() in ("show apps", "catalog", "show catalog"):
            apps = fetch_app_catalog(limit=10)
            if not apps:
                await turn_context.send_activity("No apps are configured yet.")
            else:
                await turn_context.send_activity(build_catalog_activity(apps))
            return

        parsed = parse_install_command(user_input)
        if parsed:
            app, version = parsed
            await turn_context.send_activity(f"⏳ Starting installation of {app} {version}...")
            await start_installation(user_id, app, version, turn_context)
        else:
            await turn_context.send_activity(f"You said: '{user_input}', but I didn’t detect an install request.\nTry: `install chrome 97` or click a button above.")
