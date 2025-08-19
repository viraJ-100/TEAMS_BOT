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
    payload = {"work_notes": f"Status updated to {status}"}
    response = requests.patch(
        f"{SNOW_INCIDENT_URL}/{ticket_sys_id}",
        auth=HTTPBasicAuth(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=payload
    )
    return response.json()
