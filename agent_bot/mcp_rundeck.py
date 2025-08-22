from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from config import RUNDECK_URL, RUNDECK_API_TOKEN, RUNDECK_PROJECT, RUNDECK_JOB_ID

app = FastAPI()

class RundeckRequest(BaseModel):
    app_name: str
    version: str
    download_url: str

@app.post("/mcp/rundeck/run")
def run_job(request: RundeckRequest):
    url = f"{RUNDECK_URL}/api/45/job/{RUNDECK_JOB_ID}/run"
    headers = {
        "X-Rundeck-Auth-Token": RUNDECK_API_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "options": {
            "app": request.app_name,
            "version": request.version,
            "download_url": request.download_url
        }
    }

    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code == 200:
        return {"status": "success", "data": response.json()}
    else:
        return {"status": "error", "message": response.text}
