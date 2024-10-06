# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import traceback
from datetime import datetime
from http import HTTPStatus

from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import TurnContext
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes

from bots import EchoBot
from config import DefaultConfig

# Azure Text Analytics imports
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

# Load configuration
CONFIG = DefaultConfig()

# Initialize Azure Text Analytics client
credential = AzureKeyCredential(CONFIG.API_KEY)
text_analytics_client = TextAnalyticsClient(endpoint=CONFIG.ENDPOINT_URI, credential=credential)

# Create the Bot Framework adapter
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))

# Catch-all for errors
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a user-friendly error message
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity("To continue, please fix the bot source code.")

    # Send a trace activity if running in the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=str(error),
            value_type="https://www.botframework.com/schemas/error",
        )
        await context.send_activity(trace_activity)

ADAPTER.on_turn_error = on_error

# Create the Bot
BOT = EchoBot()

# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    if req.content_type == "application/json":
        body = await req.json()

        # Perform sentiment analysis
        text_to_use = body.get("text", "")
        print(f"textToUse = {text_to_use}")

        documents = [{"id": "1", "language": "en", "text": text_to_use}]
        
        try:
            response = text_analytics_client.analyze_sentiment(documents)
            successful_responses = [doc for doc in response if not doc.is_error]

            # Prepare the response message
            response_message = "Error analyzing sentiment."
            if successful_responses:
                sentiment = successful_responses[0].sentiment
                print(f"Sentiment: {sentiment}")
                
                # Optionally, modify the response based on sentiment
                if sentiment == "positive":
                    response_message = "I'm glad to hear that!"
                elif sentiment == "negative":
                    response_message = "I'm sorry to hear that."
                else:
                    response_message = "Thanks for sharing your thoughts!"

            # Create a new activity with the response message
            activity = Activity().deserialize(body)
            activity.text = response_message  # Set the response message

        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            response_message = "There was an error analyzing your sentiment."
            activity = Activity().deserialize(body)
            activity.text = response_message  # Set error message

        auth_header = req.headers.get("Authorization", "")
        
        # Process the activity and send response back to the user
        response = await ADAPTER.process_activity(auth_header, activity, BOT.on_turn)

        return response

    return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

# Set up the web application
APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        print(f"Failed to run the app: {error}", file=sys.stderr)
        raise