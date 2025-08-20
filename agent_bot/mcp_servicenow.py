from fastapi import FastAPI
import requests
from requests.auth import HTTPBasicAuth
from config import SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, SERVICENOW_PASSWORD

app = FastAPI()

SNOW_INCIDENT_URL = f"{SERVICENOW_INSTANCE_URL}/api/now/table/incident"

@app.post("/mcp/servicenow/create")
def create_ticket(app_name: str, version: str, user_id: str):
    payload = {
        "short_description": f"Install {app_name} {version}",
        "description": f"User {user_id} requested installation of {app_name} {version}. Status: pending",
        "category": "software",
        "priority": "3"
    }
    response = requests.post(
        SNOW_INCIDENT_URL,
        auth=HTTPBasicAuth(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=payload
    )
    return response.json()


@app.post("/mcp/servicenow/update")
def update_ticket(ticket_sys_id: str, status: str):
    state_map = {
        "new": 1,
        "in_progress": 2,
        "on_hold": 3,
        "resolved": 6,
        "closed": 7
    }

    incident_state = state_map.get(status.lower(), 2)

    payload = {
        "work_notes": f"Status updated to {status}",
        "incident_state": incident_state
    }

    # Add required fields if moving to resolved
    if incident_state == 6:  # Resolved
        payload["close_code"] = "Resolved by request"
        payload["close_notes"] = "Automatically resolved by bot workflow"
        payload["caller_id"] = "guest"   # <- set a valid caller sys_id or username in your SNOW instance

    response = requests.patch(
        f"{SNOW_INCIDENT_URL}/{ticket_sys_id}",
        auth=HTTPBasicAuth(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=payload
    )
    return response.json()
