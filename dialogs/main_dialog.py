# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder import dialogs
from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import MessageFactory, TurnContext
from botbuilder.schema import InputHints

from booking_details import BookingDetails
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent
from .booking_dialog import BookingDialog

import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
import json

APPINSIGHT_IKEY = 'InstrumentationKey=e19b80c8-1f12-4737-9463-5ef5cc6de968'

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=APPINSIGHT_IKEY)
)

class MainDialog(ComponentDialog):
    def __init__(
        self, luis_recognizer: FlightBookingRecognizer, booking_dialog: BookingDialog
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)

        self._luis_recognizer = luis_recognizer
        self._booking_dialog_id = booking_dialog.id

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(booking_dialog)
        self.add_dialog(
            WaterfallDialog(
                "WFDialog", [self.intro_step, self.act_step, self.final_step]
            )
        )

        self.initial_dialog_id = "WFDialog"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )

            return await step_context.next(None)
        message_text = (
            str(step_context.options)
            if step_context.options
            else "What can I help you with today?"
        )
        prompt_message = MessageFactory.text(
            message_text, message_text, InputHints.expecting_input
        )

        return await step_context.prompt(
            TextPrompt.__name__, PromptOptions(prompt=prompt_message)
        )

    async def act_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            # LUIS is not configured, we just run the BookingDialog path with an empty BookingDetailsInstance.
            return await step_context.begin_dialog(
                self._booking_dialog_id, BookingDetails()
            )

        # Call LUIS and gather any potential booking details. (Note the TurnContext has the response to the prompt.)
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        )

        if intent == Intent.BOOK_TICKET_INTENT.value and luis_result:
            # Show a warning for Origin and Destination if we can't resolve them.
            await MainDialog._show_warning_for_unsupported_cities(
                step_context.context, luis_result
            )

            luis_result.user_input = step_context.context.activity.text
            luis_result.luis_intent = intent
            luis_result.luis_entities = {
                "destination": luis_result.destination,
                "origin": luis_result.origin,
                "start": luis_result.start,
                "end": luis_result.end,
                "budget": luis_result.budget
            }
            print('\n• Detected entities (LUIS) :', luis_result.__dict__)
            

            # Run the BookingDialog giving it whatever details we have from the LUIS call.
            return await step_context.begin_dialog(self._booking_dialog_id, luis_result)

        else:
            didnt_understand_text = (
                "Sorry, I didn't get that. Please try asking in a different way"
            )
            didnt_understand_message = MessageFactory.text(
                didnt_understand_text, didnt_understand_text, InputHints.ignoring_input
            )
            await step_context.context.send_activity(didnt_understand_message)

        return await step_context.next(None)

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # If the child dialog ("BookingDialog") was cancelled or the user failed to confirm,
        # the Result here will be null.

        if step_context.result is not None:
            result = step_context.result

            print('>> TICKET BOOKING BOT UNDERSTANDING = OK \n\n•••••\n')
            logger.warning('BOOKING_UNDERSTANDING_OK')

            # Now we have all the booking details call the booking service.

            # If the call to the booking service was successful tell the user.
            # time_property = Timex(result.travel_date)
            # travel_date_msg = time_property.to_natural_language(datetime.now())
            msg_txt = f"I have you booked to {result.destination} from {result.origin} between {result.start} and {result.end}"
            message = MessageFactory.text(msg_txt, msg_txt, InputHints.ignoring_input)
            await step_context.context.send_activity(message)

        if step_context.result is None:
            print('>> TICKET BOOKING BOT UNDERSTANDING = KO \n\n•••••\n')

            with open('dialog_content.txt') as dialog_file:
                dialog_content = json.load(dialog_file)
            #print('\n##### : ',dialog_content['user_input'])


            properties = {'custom_dimensions': {'#_user_input': dialog_content['user_input'], '#_luis_intent': dialog_content['luis_intent'], '#_luis_entities': str(dialog_content['luis_entities']), '#_final_entities': str(dialog_content['final_entities'])}}
            logger.warning('BOOKING_UNDERSTANDING_KO', extra=properties)

        prompt_message = "What else can I do for you?"
        return await step_context.replace_dialog(self.id, prompt_message)

    @staticmethod
    async def _show_warning_for_unsupported_cities(
        context: TurnContext, luis_result: BookingDetails
    ) -> None:
        if luis_result.unsupported_airports:
            message_text = (
                f"Sorry but the following airports are not supported:"
                f" {', '.join(luis_result.unsupported_airports)}"
            )
            message = MessageFactory.text(
                message_text, message_text, InputHints.ignoring_input
            )
            await context.send_activity(message)
