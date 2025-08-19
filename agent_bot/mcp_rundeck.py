from fastapi import FastAPI
import requests
import os
from config import RUNDECK_URL, RUNDECK_API_TOKEN, RUNDECK_PROJECT, RUNDECK_JOB_ID

app = FastAPI()

@app.post("/mcp/rundeck/run")
def run_job(app_name: str, version: str):
    url = f"{RUNDECK_URL}/api/45/job/{RUNDECK_JOB_ID}/run"
    headers = {
        "X-Rundeck-Auth-Token": RUNDECK_API_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "options": {
            "app": app_name,
            "version": version
        }
    }

    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code == 200:
        return {"status": "success", "data": response.json()}
    else:
        return {"status": "error", "message": response.text}
