# workflow.py
import asyncio
import requests
from db import insert_installation, update_end_time
from config import DefaultConfig

CONFIG = DefaultConfig()

MCP_SERVICENOW_URL = "http://localhost:8000/mcp/servicenow"  # adjust if FastAPI runs elsewhere


async def start_installation(user_id, app, version, turn_context):
    try:
    # Step 2: Insert into DB
        installation_id = insert_installation(user_id, app, version)

        # Create ServiceNow ticket via MCP
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
        
    # Step 3: SUPERVISOR APPROVAL

    # Step 4: SQL AND ServiceNow(pending)

    # Step 5: Notify user

    # Step 6: USER APPROVAL


    # Step 7: Simulate wait (e.g., real installation time or Rundeck job later)
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


    # Step 8: Update ServiceNow ticket(resolved) SQL(end_time)
        try:
            response = requests.post(
                f"{MCP_SERVICENOW_URL}/update",
                params={"ticket_sys_id": ticket_sys_id, "status": "resolved"}
            )
            response.raise_for_status()
            await turn_context.send_activity("✅ ServiceNow ticket updated to 'resolved'.")
        except Exception as e:
            await turn_context.send_activity(f"⚠️ Failed to update ServiceNow ticket: {e}")
            return

        # Update DB end_time
        update_end_time(installation_id)

        # Reply to user
        await turn_context.send_activity(f"🎉 Installation of {app} {version} completed successfully!")

    except Exception as e:
        return f"❌ Workflow failed: {str(e)}"
    
    # Step 9: Feedback from user