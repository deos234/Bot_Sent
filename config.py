#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import getpass

class DefaultConfig:
    """ Bot Configuration for Microsoft Bot Framework and Azure AI Language API """

    PORT = 3978  # Default to 3978

    # Microsoft App ID and Password for bot authentication
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    APP_TYPE = os.environ.get("MicrosoftAppType", "MultiTenant")
    APP_TENANTID = os.environ.get("MicrosoftAppTenantId", "")
    
    # azure authentication
    ENDPOINT_URI = input("Enter your Azure service endpoint: ")
    API_KEY = getpass.getpass("Enter your Azure API key: ")
