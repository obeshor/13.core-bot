# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext

from booking_details import BookingDetails


class Intent(Enum):
    #BOOK_FLIGHT = "BookFlight"
    #CANCEL = "Cancel"
    #GET_WEATHER = "GetWeather"
    #NONE_INTENT = "NoneIntent"
    
    BOOK_TICKET_INTENT = "AskForTickets"
    VALIDATION_INTENT = "ValidateChatBotAnswer"
    NONE_INTENT = "None"


def top_intent(intents: Dict[Intent, dict]) -> TopIntent:
    max_intent = Intent.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score

    return TopIntent(max_intent, max_value)


class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)

            intent = (
                sorted(
                    recognizer_result.intents,
                    key=recognizer_result.intents.get,
                    reverse=True,
                )[:1][0]
                if recognizer_result.intents
                else None
            )

            if intent == Intent.BOOK_TICKET_INTENT.value:
                result = BookingDetails()

                # We need to get the result from the LUIS JSON which at every level returns an array.
                to_entities = recognizer_result.entities.get("$instance", {}).get(
                    "destination", []
                )
                if len(to_entities) > 0:
                    if recognizer_result.entities.get("destination", [{"$instance": {}}])[0]:
                        result.destination = to_entities[0]["text"].capitalize()
                    else:
                        result.unsupported_airports.append(
                            to_entities[0]["text"].capitalize()
                        )

                from_entities = recognizer_result.entities.get("$instance", {}).get(
                    "origin", []
                )
                if len(from_entities) > 0:
                    if recognizer_result.entities.get("origin", [{"$instance": {}}])[0]:
                        result.origin = from_entities[0]["text"].capitalize()
                    else:
                        result.unsupported_airports.append(
                            from_entities[0]["text"].capitalize()
                        )

                budget_entities = recognizer_result.entities.get("$instance", {}).get(
                    "budget", []
                )
                if len(budget_entities) > 0:
                    result.budget = budget_entities[0]["text"]

                daterange_entities = recognizer_result.entities.get("datetime", [])
                if len(daterange_entities) > 0:
                    if (daterange_entities[0]["type"] == "daterange") & (len(daterange_entities[0]["timex"][0].split(",")) > 1):
                        result.start = daterange_entities[0]["timex"][0].split(",")[0][1:]
                        result.end = daterange_entities[0]["timex"][0].split(",")[1][:]
                    if (daterange_entities[0]["type"] == "daterange") & (len(daterange_entities[0]["timex"][0].split(",")) == 1):
                        result.start = daterange_entities[0]["timex"][0].split(",")[0][:]
                else:
                    start_entities = recognizer_result.entities.get("start", [])
                    if len(start_entities) > 0:
                        result.start = start_entities[0]["timex"][0]
                    
                    end_entities = recognizer_result.entities.get("end", [])
                    if len(end_entities) > 0:
                        result.end = end_entities[0]["timex"][0]
                    
                print('\n• travel origin = {}'.format(result.origin))
                print('• travel destination = {}'.format(result.destination))
                print('• start date = {}'.format(result.start))
                print('• end date = {}'.format(result.end))
                print('• budget = {}'.format(result.budget))

        except Exception as exception:
            print(exception)

        return intent, result
