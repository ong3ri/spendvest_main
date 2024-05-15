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


current_timestamp = func.current_timestamp()

spendvest_db = redis.Redis(host="localhost", port=6379, db=10)
print(f"testing redis commection, {spendvest_db.ping()}")


# mpesa space
def authorize_mpesa_api_access():
    pass 

def reg_ingress_saf_url():
    pass 

def send_stk_push_a():
    pass 


# Account SID and Auth Token from www.twilio.com/console
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(36), nullable=False, unique=True)
    waid = db.Column(db.String(15), nullable=False, unique=True)
    name = db.Column(db.String(20), nullable=False)
    current_menu_code = db.Column(db.String(10))
    answer_payload = db.Column(db.JSON, nullable=False)
    is_slot_filling = db.Column(db.Boolean, nullable=False, default=False)
    current_slot_count = db.Column(db.Integer, nullable=False, default=0)
    slot_quiz_count = db.Column(db.Integer, nullable=False, default=0)
    current_slot_handler = db.Column(db.String(30))
    created_at = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.Float, nullable=False)


class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(36), nullable=False, unique=True)
    menu_code = db.Column(db.String(10), nullable=False)
    menu_description = db.Column(db.String(100))
    question_payload = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.Float, nullable=False)

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
                        0: "Register!\n\nWould you like us to register your number ?\n Yes or No",
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
                        1: "Confirm number, by repeating it"
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
                        0: "Enter command to proceed"
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
def whatsapp_webhook():
    ingress_payload = request.values 
    bot_instance = WhatsappBot(ingress_payload['WaId'], ingress_payload["ProfileName"])
    bot_instance.ingest_message(ingress_payload['Body'].lower())

    if bot_instance.is_first_interaction():
        print(f"first contact initiated")
        # Check if there's an existing session for the user
        existing_session = Session.query.filter_by(waid=bot_instance.waid).first()

        # If an existing session is found, delete it
        if existing_session:
            db.session.delete(existing_session)
            db.session.commit()
            print("Existing session deleted.")

        # Create a new session
        new_session = Session()
        new_session.waid = bot_instance.waid
        new_session.uid = generate_uid()
        new_session.name = bot_instance.user_name
                
        # slot filling init
        new_session.is_slot_filling = True
        new_session.current_menu_code = "LBT"
        new_session.current_slot_handler = "lbt_handler"

        new_session.current_slot_count = 0
        new_session.slot_quiz_count = 1
        new_session.answer_payload= {}
        
        new_session.created_at = time.time()
        new_session.updated_at = time.time()
        
        all_session = Session.query.all()
        print(f"current session count {all_session}")


        try:
            db.session.add(new_session)
            db.session.commit()
            print("New session created.")
        except Exception as e: 
            print(f"Error occurred while loading the session: {e}, entry count is {all_session}")

        slot_details = bot_instance.fetch_slot_details()
        bot_instance.process_handler(slot_details)

        bot_instance.step_slot()
        return bot_instance.show_current_slot_quiz(slot_details)

    else:
        # continuing user
        if bot_instance.is_slot_filling():
            print(f"user is slot filling, current input is : {bot_instance.current_input_message}")
            slot_details = bot_instance.fetch_slot_details()

            bot_instance.process_handler(slot_details)

            bot_instance.step_slot()
            return bot_instance.show_current_slot_quiz(slot_details)
        else:
            bot_instance.load_handler("start_handler")
            return bot_instance.show_start_message()


# whatsapp bot class
class WhatsappBot:
    """This object helps with non-destructive assembly of spendvest bot"""

    def __init__(self, waid, user_name):
        print(f"Bot loaded for WaId: {waid}")
        self.waid = waid
        self.current_input_message = ""
        self.current_output_message = ""
        self.user_name = user_name

    def ingest_message(self, input_message):
        self.current_input_message = input_message.lower()

    def output_message(self):
        resp = MessagingResponse()
        resp.message(self.current_output_message)
        return str(resp)

    def is_first_interaction(self):
        session = Session.query.filter_by(waid=self.waid).first()
        return session is None



    def show_start_message(self):
        start_message = (
            f"Welcome {self.user_name}\n\n"
            "Select the following commands to proceed:\n\n"
            "1. /sm\nfor send money\n\n"
            "2. /lp\nfor lipa pochi\n\n"
            "3. /lbt\nfor buy goods and services till\n\n"
            "4. /lbp\nfor paybill till\n\n"
            "To select any, enter /command"
        )
        self.current_output_message = start_message
        return self.output_message()

    def load_handler(self, handler_name):
        session = Session.query.filter_by(waid=self.waid).first()
        if session:
            session.current_slot_handler = handler_name
            handler_code_map = {
                "ru_handler": "RU",
                "sm_handler": "SM",
                "lp_handler": "LP",
                "lbt_handler": "LBT",
                "lbp_handler": "LBP",
                "start_handler": "ST"
            }
            session.current_menu_code = handler_code_map.get(handler_name, "")
            db.session.commit()
            print(f"Processing handler {handler_name}")
        else:
            print("No session found for the given WhatsApp ID.")

    def null_handler(self):
        session = Session.query.filter_by(waid=self.waid).first()
        if session:
            session.current_slot_handler = None
            db.session.commit()
        else:
            print("No session found for the given WhatsApp ID.")



    def is_slot_filling(self):
        session = Session.query.filter_by(waid=self.waid).first()
        return session.is_slot_filling if session else False
    
    def fetch_slot_details(self):
        session = Session.query.filter_by(waid=self.waid).first()
        if session:
            menu = Menu.query.filter_by(menu_code=session.current_menu_code).first()
            if menu:
                return {
                    "menu_code": session.current_menu_code,
                    "slot_count": session.current_slot_count,
                    "quiz_count": session.slot_quiz_count,
                    "current_slot_handler": session.current_slot_handler,
                    "quiz_pack": menu.question_payload
                }
        return "No session details"

    def show_current_slot_quiz(self, slot_details):
        count_ = slot_details['slot_count']
        self.current_output_message = slot_details['quiz_pack'][str(count_)]
        print(f"Updated current_output_message is: {self.current_output_message}")
        return self.output_message()


    def save_answer(self, payload):
        pass 

    def step_slot(self):
        session = Session.query.filter_by(waid=self.waid).first()
        if session:
            if session.current_slot_count < session.slot_quiz_count:
                session.current_slot_count += 1
                db.session.commit()
                print(f"Incremented slot count to {session.current_slot_count}")
            else:
                print("Current slot count is already at maximum.")
        else:
            print("No session found for the given WhatsApp ID.")


    def complete_slot_filling(self):
        session = Session.query.filter_by(waid=self.waid).first()
        if session:
            session.is_slot_filling = False
            session.current_menu_code = "ST" 
            session.current_slot_handler = "st_handler"

            session.current_slot_count = 0
            session.slot_quiz_count = 0
            session.answer_payload = {}

            db.session.commit()
        else:
            print("No session found for the given WhatsApp ID.")
         
    def is_valid_yes_or_no(reg_ans):
        """Check if the input is 'yes' or 'no' after converting to lowercase."""
        reg_ans = reg_ans.lower()
        return reg_ans in ["yes", "no"] 

    def is_valid_phone_number(phone_number):
        """Validate phone numbers in the format +254XXXXXXXXX or 07XXXXXXXX."""
        pattern = re.compile(r"^(?:\+254|0)?7\d{8}$")
        return bool(pattern.match(phone_number))

    def is_valid_till_number(till_number):
        """Validate till numbers which are 6 to 7 digits."""
        pattern = re.compile(r"^\d{6,7}$")
        return bool(pattern.match(till_number))

    def is_valid_paybill_number(paybill_number):
        """Validate paybill numbers which are 5 to 6 digits."""
        pattern = re.compile(r"^\d{5,6}$")
        return bool(pattern.match(paybill_number))

    def process_handler(self, slot_details):
        handler = slot_details['current_slot_handler']
        user_session = Session.query.filter_by(waid=self.waid).first()
        ans_payload = user_session.answer_payload
        print(f"fetched user session answer is , {ans_payload}")
        ans = {f"{slot_details['slot_count']}": self.current_input_message}

        if handler == "ru_handler":
            if ans_payload == {}:
                updated_ans = {}
                updated_ans.update(ans)
                print(f"in ru_handler, answer map is , {updated_ans}")
                db.session.ans_payload = updated_ans
                db.session.add(user_session)
                try:
                    db.session.commit()
                except Exception as e:
                    print(f"error in updating answer to table, {e}")
                pass
            else:
                existing_ans = user_session.ans_payload
                existing_ans.update(ans)
                print(f"in ru_handler 2, answer map is , {existing_ans}")
                db.session.ans_payload = existing_ans
                db.session.add(user_session)
                try:
                    db.session.commit()
                except Exception as e:
                    print(f"error in updating answer to table")
                
                
             
    def show_about_message(self):
        about_information = (
            "Welcome to Spendvest bot\n"
            "This bot will help you to request payment tasks for Mpesa recipients"
        )
        self.current_output_message = about_information
        return self.output_message()




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
