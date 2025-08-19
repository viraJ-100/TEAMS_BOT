#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from dotenv import load_dotenv

load_dotenv() 

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

    # MySQL Configuration
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "root@1234")
    DB_NAME = os.environ.get("DB_NAME", "bot_db")



SERVICENOW_INSTANCE_URL = os.environ.get("SERVICENOW_INSTANCE_URL", "https://dev340191.service-now.com/")
SERVICENOW_USERNAME = os.environ.get("SERVICENOW_USERNAME", "admin")
SERVICENOW_PASSWORD = os.environ.get("SERVICENOW_PASSWORD", "5x$XyQYtU9!u")


# Rundeck Config
RUNDECK_URL = os.environ.get("RUNDECK_URL", "http://localhost:4440")
RUNDECK_API_TOKEN = os.environ.get("RUNDECK_API_TOKEN", "LT0PQl8WAy1dsmzVPfWEv7qAmiQ2dji3")
RUNDECK_PROJECT = os.environ.get("RUNDECK_PROJECT", "AppInstaller")
RUNDECK_JOB_ID = os.environ.get("RUNDECK_JOB_ID", "b503f4fb-112d-4008-8204-8b2e633dd2b9")

