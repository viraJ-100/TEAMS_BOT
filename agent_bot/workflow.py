# workflow.py
import requests
from db import insert_installation, update_end_time, update_ticket_id, update_approval_req

MCP_SERVICENOW_URL = "http://localhost:8000/mcp/servicenow"
MCP_RUNDECK_URL = "http://localhost:8001/mcp/rundeck"

# keep track of pending approvals
pending_approvals = {}  # {user_id: {...}}

async def start_installation(user_id, app, version, turn_context):
    """Start install request, create ticket, then wait for approval"""
    try:
        # Step 2: Insert into DB
        installation_id = insert_installation(user_id, app, version)

        # Create ServiceNow ticket via MCP
        response = requests.post(
            f"{MCP_SERVICENOW_URL}/create",
            params={"app_name": app, "version": version, "user_id": user_id}
        )
        response.raise_for_status()
        ticket = response.json()
        ticket_sys_id = ticket.get("result", {}).get("sys_id", "UNKNOWN")
        ticket_number = ticket.get("result", {}).get("number")

        await turn_context.send_activity(
            f"📋 ServiceNow ticket created for {app} {version} (Sys ID: {ticket_number})."
        )

        update_ticket_id(installation_id, ticket_number)

    # Step 3: SUPERVISOR APPROVAL
    #default approval status


        pending_approvals[user_id] = {
            "installation_id": installation_id,
            "app": app,
            "version": version,
            "ticket_sys_id": ticket_sys_id,
        }

        await turn_context.send_activity(
            f"👨‍💼 Supervisor approval required: Do you approve installation of {app} {version}? (approve/reject)"
        )
        return

    except Exception as e:
        await turn_context.send_activity(f"❌ Workflow failed at start: {str(e)}")


async def continue_installation_sup(user_id,approved: bool, turn_context):
    """Continue workflow after supervisor decision"""
    # Step 4: SQL AND ServiceNow(pending) 
    if user_id not in pending_approvals:
        await turn_context.send_activity("⚠️ No pending approval found.")
        return

    data = pending_approvals[user_id]  # remove from queue
    
    app = data["app"]
    version = data["version"]

    if not approved:
        update_approval_req(data["installation_id"], "Rejected")
        await turn_context.send_activity("❌ Installation request rejected by supervisor.")
    # Update DB end_time
        update_end_time(data["installation_id"])
        return

    # Mark approved
    update_approval_req(data["installation_id"], "Approved")
    await turn_context.send_activity("✅ Installation approved by supervisor. Proceeding...")

 
    try:
        response = requests.post(
            f"{MCP_SERVICENOW_URL}/update",
            params={"ticket_sys_id": data["ticket_sys_id"], "status": "in_progress"}
        )
        response.raise_for_status()
        await turn_context.send_activity("🔄 ServiceNow ticket updated to 'in_progress'.")
    except Exception as e:
        await turn_context.send_activity(f"⚠️ Failed to update ServiceNow ticket: {e}")
        return

    # Step 5: Notify user
    await turn_context.send_activity(
            f"👨‍💼 Continue with installation of {app} {version}? (yes/no)"
        )

    # Step 6: USER APPROVAL
async def continue_installation_user(user_id,approved: bool, turn_context):
    """Continue workflow after supervisor decision"""
    # Step 4: SQL AND ServiceNow(pending) 
    if user_id not in pending_approvals:
        await turn_context.send_activity("⚠️ No pending approval found.")
        return

    data_user = pending_approvals.pop(user_id)  # remove from queue 
    app = data_user["app"]
    version = data_user["version"]

    if not approved:
        # update_approval_req(pending_approvals["installation_id"], "Rejected")
        await turn_context.send_activity("❌ Installation request rejected by user.")
    # Update DB end_time
        update_end_time(data_user["installation_id"])
        return
    
    await turn_context.send_activity("✅ Installation approved by user. Proceeding...")


# Step 7: Rundeck job 
    await turn_context.send_activity("⚙️ Installation in progress...")
    download_url = "https://github.com/git-for-windows/git/releases/download/v2.51.0.windows.1/Git-2.51.0-64-bit.exe"
        # 3. Run Rundeck Job instead of sleep
    rundeck_response = requests.post(
        "http://localhost:8001/mcp/rundeck/run",
        json={"app_name": app, "version": version, "download_url": download_url}
    )
    if rundeck_response.status_code == 200:
        await turn_context.send_activity(f"⚙️ Installation triggered on Rundeck for {app} {version}")
    else:
        await turn_context.send_activity(f"❌ Rundeck job failed: {rundeck_response.text}")    

# Step 8: Update ServiceNow ticket(resolved) SQL(end_time)
    try:
        response = requests.post(
            f"{MCP_SERVICENOW_URL}/update",
            params={"ticket_sys_id": data_user["ticket_sys_id"], "status": "resolved"}
        )
        response.raise_for_status()
        await turn_context.send_activity("✅ ServiceNow ticket updated to 'resolved'.")
    except Exception as e:
        await turn_context.send_activity(f"⚠️ Failed to update ServiceNow ticket: {e}")
        return

    # Update DB end_time
    update_end_time(data_user["installation_id"])

    # Reply to userAC
    await turn_context.send_activity(f"🎉 Installation of {app} {version} completed successfully!")

    
    # Step 9: Feedback from user