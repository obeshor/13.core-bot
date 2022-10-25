#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "a396152c-cbf4-4ae1-b7d3-59680905189c")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "TBe8Q~r2QURUmVgGdStT5plKPiMDyrC4JZC1adnz")
    LUIS_APP_ID = os.environ.get("LuisAppId", "84caf03a-4048-4a6f-b502-c386c030394e")
    LUIS_API_KEY = os.environ.get("LuisAPIKey", "64f61e3e6fdc4a8d802956a911f88386")
    # LUIS endpoint host name, ie "westus.api.cognitive.microsoft.com"
    LUIS_API_HOST_NAME = os.environ.get("LuisAPIHostName", "westus.api.cognitive.microsoft.com")
