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
from models  import Menu, MpesaCustomer
import uuid

current_timestamp = func.current_timestamp()

# Account SID and Auth Token from www.twilio.com/console
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy()

def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid


slot_handlers = ["ru_handler", "sm_handler", "lp_handler", "lbt_handler", "lbp_handler", "start_handler"]

# whatsapp ingress endpoint
@app.route("/whatsapp", methods=["POST"])
def new_webhook():
    in_data = request.values 
    user_waid = in_data.get('WaId')
    user_name = in_data.get('ProfileName')
    print(f"incoming payload is , {in_data}")

    if Session.is_first_time_contact(user_waid):
        print(f"first time contact")
    else:
        print(f"not existing, creating one") 
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

        # first processing
        pass


def output_bot_message(message):
    resp = MessagingResponse()
    resp.message(message)
    m = str(resp)
    print(f"'returning bot output {m}")
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
