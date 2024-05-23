from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
import urllib
import redis
import random
import string 
import time
from sqlalchemy.sql import func
import re
import json 

from blu import Session
from payments2 import send_user_stk

import uuid

current_timestamp = func.current_timestamp()

# Account SID and Auth Token from www.twilio.com/console
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)


class MpesaCustomer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(36), nullable=False, unique=True)
    mpesa_number = db.Column(db.String(15), nullable=False, unique=True)
    created_at = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.Float, nullable=False)

    @staticmethod
    def get_all_mpesa_customers():
        return MpesaCustomer.query.all()

    @staticmethod
    def add_mpesa_customer(mpesa_number):
        uid = str(uuid.uuid4())
        current_time = time.time()
        new_customer = MpesaCustomer(
            uid=uid,
            mpesa_number=mpesa_number,
            created_at=current_time,
            updated_at=current_time
        )
        db.session.add(new_customer)
        db.session.commit()
        return new_customer

    @staticmethod
    def test_add_10_users():
        for _ in range(10):
            mpesa_number = "2547" + ''.join([str(random.randint(0, 9)) for _ in range(8)])
            MpesaCustomer.add_mpesa_customer(mpesa_number)
        print("10 users added successfully") 
    
    
class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(36), nullable=False, unique=True)
    menu_code = db.Column(db.String(10), nullable=False)
    menu_description = db.Column(db.String(100))
    question_payload = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.Float, nullable=False)
    
    @staticmethod
    def load_question_pack(menu_code):
        menu = Menu.query.filter_by(menu_code=menu_code).first()
        return menu.question_payload

class RequestTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(36), nullable=False, unique=True)
    client_id = db.Column(db.String(36), nullable=False, unique=True)
    service_description = db.Column(db.String(100))
    service_payload = db.Column(db.JSON, nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.Float, nullable=False)



def create_tables():
    """
    Create the Session and Menu tables in the database.
    """
    with db.engine.connect() as connection:
        db.metadata.create_all(connection)
        print("Tables created successfully.")

def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid

def load_menu_table():
    try:
        if not Menu.query.all():
            menu_data = [
                {
                    "uid": generate_uid(),
                    "menu_code": "RU",
                    "menu_description": "Request register user task",
                    "question_payload": {
                        0: "Register!\n\nWould you like us to register this number for Mpesa service?\n Yes or No",
                        1: "Confirm registeration, by re-entering previous answer"
                    },
                    "created_at": time.time(),
                    "updated_at": time.time()
                },
                {
                    "uid": generate_uid(),
                    "menu_code": "SM",
                    "menu_description": "Request send money task",
                    "question_payload": {
                        0: "Send money!\n\nEnter recipient Mpesa phone number",
                        1: "Confirm number, by repeating it",
                        2: "Enter amount to send"
                    },
                    "created_at": time.time(),
                    "updated_at": time.time()
                },
                {
                    "uid": generate_uid(),
                    "menu_code": "LP",
                    "menu_description": "Request lipa na pochi la biashsara task",
                    "question_payload": {
                        0: "Lipa pochi!\n\nEnter recipient Mpesa phone number",
                        1: "Confirm number, by repeating it"
                    },
                    "created_at": time.time(),
                    "updated_at": time.time()
                },
                {
                    "uid": generate_uid(),
                    "menu_code": "LBT",
                    "menu_description": "Request lipa na Buy Goods and Services task",
                    "question_payload": {
                        0: "Buy Goods and Services!\n\nEnter recipient Mpesa buy goods and services number",
                        1: "Confirm number, by repeating it"
                    },
                    "created_at": time.time(),
                    "updated_at": time.time()
                },
                {
                    "uid": generate_uid(),
                    "menu_code": "LBP",
                    "menu_description": "Request lipa na paybill task",
                    "question_payload": {
                        0: "Paybill!\n\nEnter recipient Mpesa paybill number",
                        1: "Confirm number, by repeating it"
                    },
                    "created_at": time.time(),
                    "updated_at": time.time()
                },
                {
                    "uid": generate_uid(),
                    "menu_code": "ST",
                    "menu_description": "Choose command to execute",
                    "question_payload": {
                        0: "Select the following commands to proceed: \n\n0./reg\nfor register Whatsapp number for Mpesa services\n\n1./sm\nfor send money\n\n2./lp\nfor lipa pochi\n\n3./lbt\nfor buy goods and services till\n\n4./lbp\nfor paybill till\n\nTo select any enter /command or number"
                    },
                    "created_at": time.time(),
                    "updated_at": time.time()
                }
            ]

            print(f"Loading menu table with data: {menu_data}")

            for data in menu_data:
                menu = Menu(
                    uid=data['uid'],
                    menu_code=data['menu_code'],
                    menu_description=data['menu_description'],
                    question_payload=data['question_payload'],
                    created_at=data['created_at'],
                    updated_at=data['updated_at']
                )
                db.session.add(menu)

            db.session.commit()
            print(f"Menu data loaded successfully")

        else:
            print(f"Menu table is not empty, maintaining existing data {Menu.query.all()}")
    except Exception as e:
        print(f"Error occurred while loading menu data: {e}")


slot_handlers = ["ru_handler", "sm_handler", "lp_handler", "lbt_handler", "lbp_handler", "start_handler"]

# whatsapp ingress endpoint
@app.route("/whatsapp", methods=["POST"])
def web_hook():
    in_data = request.values 
    user_waid = in_data.get('WaId')
    user_name = in_data.get('ProfileName')
    print(f"incoming payload is , {in_data}")

    if Session.is_first_time_contact(user_waid):
        print(f"First time contact")

        if Session.is_slot_filling(user_waid):
            print(f"user is slot filling")
            current_handler = Session.get_session(user_waid)[b'current_slot_handler'].decode('utf-8')
            print(f"current handler is : {current_handler}")
            client_input = in_data.get('Body').lower()
            if current_handler == "st_handler":
                if client_input in ['/reg', '/sm', '/lp', '/lbt', '/lbp', '/st', '/cancel']:
                    if client_input == '/reg':
                        Session.load_handler(user_waid,"ru_handler", "RU", 0, 2)
                        # ask actual first question
                        curr_slot_details = Session.fetch_slot_details(user_waid)
                        menu_code = curr_slot_details['menu_code']
                        quiz_pack = Menu.load_question_pack(menu_code)
                        quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                        Session.step_slotting(user_waid, quiz_pack)
                        return output_bot_message(quiz)
                    
                    elif client_input == '/sm':
                        Session.load_handler(user_waid, "sm_handler", "SM",0, 3)
                        curr_slot_details = Session.fetch_slot_details(user_waid)
                        menu_code = curr_slot_details['menu_code']
                        quiz_pack = Menu.load_question_pack(menu_code)
                        quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                        Session.step_slotting(user_waid, quiz_pack)
                        return output_bot_message(quiz)
                    
                    elif client_input == "/lp":
                        message = "You have selected Lipa Pochi task"
                        return output_bot_message(message)
                        
                    elif client_input == "/lbt":
                        message = "You have selected buy goods and services task"
                        return output_bot_message(message)
                        
                    elif client_input == "/lbp":
                        message = "You have selected paybill task"
                        return output_bot_message(message)
                    
                    elif client_input == "/st":
                        print(f"processing /st command")
                        Session.load_handler(user_waid,"st_handler", "ST", 0, 1)
                        curr_slot_details = Session.fetch_slot_details(user_waid)
                        menu_code = curr_slot_details['menu_code']
                        quiz_pack = Menu.load_question_pack(menu_code)
                        quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                        # Session.step_slotting(user_waid, quiz_pack)
                        return output_bot_message(quiz)

                else:
                    return output_bot_message("Enter comand /st to proceed")
                 
            elif current_handler == "ru_handler":
                curr_slot_details = Session.fetch_slot_details(user_waid)          
                menu_code = curr_slot_details['menu_code']
                count_ = curr_slot_details['slot_count']
                print(f"processing menu code {menu_code}, current_count {count_}")
                print(f"type for count_ {type(count_)}")

                
                if is_valid_yes_or_no(client_input):
                    print(f"{client_input}, is valid input")
                    Session.save_answer(user_waid, count_, client_input)
                    if client_input == "yes":

                        if Session.complete_reg_slotting(user_waid):
                            message = f"Your registeration using +{user_waid}\n\nfor spendvest is complete,\n\n"
                            Session.load_handler(user_waid, 'st_handler', 'ST',0, 1)
                            existing_customer = MpesaCustomer.query.filter_by(mpesa_number=user_waid).first()
                            
                            if existing_customer:
                                print(f"customer is existing")
                                Session.clear_answer_slot(user_waid)
                                message = f"This number is already registerd"
                            else:
                                MpesaCustomer.add_mpesa_customer(user_waid)

                            return output_bot_message(message)
                        
                        else:
                            quiz_pack = Menu.load_question_pack(menu_code)
                            quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                    
                            Session.step_slotting(user_waid, quiz_pack)
                
                            return output_bot_message(quiz)
 
                    elif client_input == "no":
                        print(f"Customer has cancelled")
                        Session.clear_answer_slot(user_waid)
                        message = f"You have cancelled the registeration process" 
                        Session.load_handler(user_waid, "st_handler", "ST", 1, 1)
                        return output_bot_message(message)
                
                else:
                    print(f"{client_input}, is invalid")
                    message = "Error\n\nThat input was invalid"
                    return output_bot_message(message)
                
            elif current_handler == "sm_handler":
                curr_slot_details = Session.fetch_slot_details(user_waid)          
                menu_code = curr_slot_details['menu_code']
                count_ = curr_slot_details['slot_count']
                print(f"processing menu code {menu_code}, current_count {count_}")
                print(f"type for count_ {type(count_)}")
                count_ = int(count_)

                if count_ == 0 or count_ == 1:
                    # process quiz1
                    if is_valid_phone_number(client_input):
                        print(f"{client_input}, is valid")
                    
                        Session.save_answer(user_waid, count_, client_input)
                    
                        if Session.complete_sm_slotting(user_waid):
                            message = f"Your request for Send Money task has been submitted,\n\nPlease wait for Mpesa prompt on +{user_waid}\n\nThen enter your Mpesa PIN\n\nThank you 😊"
                            Session.load_handler(user_waid, 'st_handler', 'ST', 0, 1)
                            Session.clear_answer_slot(user_waid)

                            print(f"user number is : {user_waid}")
                            send_user_stk(user_waid, 50)
                            return output_bot_message(message)
                        else:
                            quiz_pack = Menu.load_question_pack(menu_code)
                            quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                    
                            Session.step_slotting(user_waid, quiz_pack)
                    
                    
                        return output_bot_message(quiz)
                    else:
                        print(f"{client_input}, is invalid")
                        message = "Error\n\nThat input was invalid"
                        return output_bot_message(message) 
                     
                elif count_ == 2:
                    if is_valid_payment_amount(client_input):
                        print(f"valid payment number : {client_input}")
                        Session.save_answer(user_waid, count_, client_input)
                        if Session.complete_sm_slotting(user_waid):
                            message = f"Your request for Send Money task has been submitted,\n\nPlease wait for Mpesa prompt on +{user_waid}\n\nThen enter your Mpesa PIN\n\nThank you 😊"
                            Session.load_handler(user_waid, 'st_handler', 'ST', 0, 1)
                            Session.clear_answer_slot(user_waid)

                            print(f"user number is : {user_waid}")
                            send_user_stk(user_waid, 50)
                            return output_bot_message(message)
                        else:
                            quiz_pack = Menu.load_question_pack(menu_code)
                            quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                    
                            Session.step_slotting(user_waid, quiz_pack)
                            return output_bot_message(quiz)
                    else:
                        print(f"{client_input}, is invalid")
                        message = "Error\n\nThat input was invalid"
                        return output_bot_message(message)  
                 
                    
                

                 
            elif current_handler == "lp_handler":
                pass
               
            elif current_handler == "lbt_handler":
                pass
                
            elif current_handler == "lbp_handler":
                pass           
        else:
            print(f"user is not slot filling")
    else:
        print(f"not first time contact, creating new session")
        
        new_user_session = Session(uid=generate_uid(), 
                           waid=user_waid,
                           name=in_data.get('ProfileName'), 
                           current_menu_code='ST', 
                           answer_payload='[]', 
                           is_slot_filling=0, 
                           current_slot_count=0, 
                           slot_quiz_count=len(Menu.load_question_pack('ST')), 
                           current_slot_handler='st_handler')
        new_user_session.save()
        # Session.set_slot_filling_on(user_waid)
        Session.set_slot_filling_on(user_waid)
        quiz_pack = Menu.load_question_pack('ST')
        print(f"current quiz pack, {quiz_pack}")
        quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
        print(f"created session with slot_filling on is , {Session.get_session(user_waid)}")
        return output_bot_message(quiz)
    
     
def output_bot_message(message):
    resp = MessagingResponse()
    resp.message(message)
    return str(resp)


def is_valid_yes_or_no(reg_ans):
    """Check if the input is 'yes' or 'no' after converting to lowercase."""
    reg_ans = reg_ans.lower()
    return reg_ans in ["yes", "no"] 

def is_valid_phone_number(phone_ans):
    phone_pattern = re.compile(r'^\d{10,15}$')
    return bool(phone_pattern.match(phone_ans))

def is_valid_paybill(paybill_ans):
    paybill_pattern = re.compile(r'^\d{5,10}$')
    return bool(paybill_pattern.match(paybill_ans))

def is_valid_till(till_ans):
    till_pattern = re.compile(r'^\d{5,10}$')
    return bool(till_pattern.match(till_ans))

def is_valid_payment_amount(payment):
    # Define the regex pattern for a valid payment amount
    pattern = r'^[\$\€\£]?\s*-?\d{1,3}(?:[,.\s]?\d{3})*(?:[.,]\d{1,2})?$'

    # Check if the input matches the pattern
    if re.match(pattern, payment):
        return True
    else:
        return False

# mpesa
@app.route("/mpesa_callback", methods=['POST'])
def process_callback():
    print(f"recieved callback data is, {request.get_json()}")

    return 'ok'


@app.route("/mpesa_callback_timeout", methods=['POST'])
def process_callback_timeout():
    print(f"recieved callback data is, {request.get_json()}")

    return 'ok'


# Get all sessions
@app.route('/sessions', methods=['GET'])
def get_sessions():
    sessions = Session.query.all()
    session_list = [{'id': session.id, 'name': session.name} for session in sessions]
    return jsonify({'sessions': session_list})

# Get single session
@app.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    session = Session.query.get(session_id)
    if session:
        return jsonify({'id': session.id, 'name': session.name})
    else:
        return jsonify({"error": "Session not found"}), 404

# Create session
@app.route('/sessions', methods=['POST'])
def create_session():
    name = request.json.get('name')
    if not name:
        return jsonify({"error": "Name cannot be blank"}), 400

    session_test = Session(name=name)
    db.session.add(session_test)
    db.session.commit()
    return jsonify({"message": "Session created successfully", "id": session_test.id}), 201

# Update session
@app.route('/sessions/<int:session_id>', methods=['PATCH'])
def update_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    name = request.json.get('name')
    if not name:
        return jsonify({"error": "Name cannot be blank"}), 400

    session.name = name
    db.session.commit()
    return jsonify({"message": "Session updated successfully", "id": session.id}), 200

# Delete session
@app.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    db.session.delete(session)
    db.session.commit()
    return jsonify({"message": "Session deleted successfully", "id": session.id}), 200

if __name__ == "__main__":
    with app.app_context():
        create_tables()
        load_menu_table()
    app.run(debug=True, port=5080)
