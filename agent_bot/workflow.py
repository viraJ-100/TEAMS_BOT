# workflow.py
import asyncio
import requests
from db import insert_installation, update_end_time
from config import DefaultConfig

CONFIG = DefaultConfig()

MCP_SERVICENOW_URL = "http://localhost:8000/mcp/servicenow"  # adjust if FastAPI runs elsewhere


async def start_installation(user_id, app, version, turn_context):
    try:
    # Step 1: Insert into DB
        installation_id = insert_installation(user_id, app, version)

        # Step 2: Create ServiceNow ticket via MCP
        try:
            response = requests.post(
                f"{MCP_SERVICENOW_URL}/create",
                params={"app_name": app, "version": version, "user_id": user_id}
            )
            response.raise_for_status()
            ticket = response.json()
            ticket_sys_id = ticket.get("result", {}).get("sys_id", "UNKNOWN")

            await turn_context.send_activity(f"📋 ServiceNow ticket created for {app} {version} (Sys ID: {ticket_sys_id}).")

        except Exception as e:
            await turn_context.send_activity(f"⚠️ Failed to create ServiceNow ticket: {e}")
            return

        # Step 3: Simulate wait (e.g., real installation time or Rundeck job later)
        await turn_context.send_activity("⚙️ Installation in progress...")
        # 3. Run Rundeck Job instead of sleep
        rundeck_response = requests.post(
            "http://localhost:8001/mcp/rundeck/run",
            json={"app_name": app, "version": version}
        )
        if rundeck_response.status_code == 200:
            await turn_context.send_activity(f"⚙️ Installation triggered on Rundeck for {app} {version}")
        else:
            await turn_context.send_activity(f"❌ Rundeck job failed: {rundeck_response.text}")


        # Step 4: Update ServiceNow ticket
        try:
            response = requests.post(
                f"{MCP_SERVICENOW_URL}/update",
                params={"ticket_sys_id": ticket_sys_id, "status": "completed"}
            )
            response.raise_for_status()
            await turn_context.send_activity("✅ ServiceNow ticket updated to 'completed'.")
        except Exception as e:
            await turn_context.send_activity(f"⚠️ Failed to update ServiceNow ticket: {e}")
            return

        # Step 5: Update DB end_time
        update_end_time(installation_id)

        # Step 6: Reply to user
        await turn_context.send_activity(f"🎉 Installation of {app} {version} completed successfully!")

    except Exception as e:
        return f"❌ Workflow failed: {str(e)}"