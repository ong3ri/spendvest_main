from dataclasses import dataclass
from typing import Callable, Optional, Union
import re
from twilio.twiml.messaging_response import MessagingResponse

from blu import Session
     
def output_bot_message(message):
    resp = MessagingResponse()
    resp.message(message)
    m = str(resp)
    print(f"'returning bot output {m}")
    return str(resp)

@dataclass
class QuestionState():
    valid_input: re.Pattern
    menu_message: str
    handler: Callable
    next_state: Union['QuestionState', None]

    def handle_input(
            self,
            input_character,
    ) -> Optional['QuestionState']:
        match = self.valid_input.match(input_character)

        if match:
            successful_processing = self.handler(input_character)
            return successful_processing
        
        raise Exception("Invalid input.")


    def get_menu_message(self, message: str):
        output_bot_message(message)
    
@dataclass
class CircularQuestionList():
    head: QuestionState
    current_step: QuestionState
    trigger_input: str

    def append(self, valid_input, menu_message, handler):
        new_question = QuestionState(
            valid_input=valid_input,
            menu_message=menu_message,
            handler=handler,
            next_state=None
        )
        if self.head == None:
            self.head = new_question
            self.head.next_state = self.head
            self.current_step = self.head
        else:
            current = self.head
            while current.next_state != self.head and current.next_state != None:
                current = current.next_state
            current.next_state = new_question
            new_question.next_state = self.head

    def set_current_step(self, step: QuestionState):
        self.current_step = step
        # Set slot in redis
        

    def handle_input(self, input_character: str):
        success = self.current_step.handle_input(
            input_character=input_character
        )

        if success and self.current_step.next_state != None:
            self.set_current_step(self.current_step.next_state)

        return success
    
# Send Money
# send_money = CircularQuestionList()

# Lipa Pochi
# lipa_pochi = CircularQuestionList()

# Buy Goods Till
# buy_goods_till = CircularQuestionList()

# Paybill
# paybill_till = CircularQuestionList()
