from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, Boolean, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
import time
import random

# Create an engine
engine = create_engine('sqlite:///site.db')  # Replace with your actual database URL

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a Session
session = Session()

# Create a base class for your models
Base = declarative_base()

class MpesaCustomer(Base):
    __tablename__ = 'mpesa_customers'
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), nullable=False, unique=True)
    mpesa_number = Column(String(15), nullable=False, unique=True)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)

    @staticmethod
    def get_all_mpesa_customers():
        return session.query(MpesaCustomer).all()

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
        session.add(new_customer)
        session.commit()
        return new_customer

    @staticmethod
    def test_add_10_users():
        for _ in range(10):
            mpesa_number = "2547" + ''.join([str(random.randint(0, 9)) for _ in range(8)])
            MpesaCustomer.add_mpesa_customer(mpesa_number)
        print("10 users added successfully") 

class Menu(Base):
    __tablename__ = 'menus'
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), nullable=False, unique=True)
    menu_code = Column(String(10), nullable=False)
    menu_description = Column(String(100))
    question_payload = Column(JSON, nullable=False)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)
    
    @staticmethod
    def load_question_pack(menu_code):
        return session.query(Menu).filter_by(menu_code=menu_code).first().question_payload

class RequestTask(Base):
    __tablename__ = 'request_tasks'
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), nullable=False, unique=True)
    client_id = Column(String(36), nullable=False, unique=True)
    service_description = Column(String(100))
    service_payload = Column(JSON, nullable=False)
    completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)

# Function to create tables
def create_tables():
    """
    Create the MpesaCustomer, Menu, and RequestTask tables in the database.
    """
    Base.metadata.create_all(engine)
    print("Tables created successfully.")

# Helper function to generate unique IDs
def generate_uid():
    return str(uuid.uuid4())

# Function to load menu table with initial data
def load_menu_table():
    try:
        if not session.query(Menu).all():
            menu_data = [
                {
                    "uid": generate_uid(),
                    "menu_code": "RU",
                    "menu_description": "Request register user task",
                    "question_payload": {
                        0: "Register!\n\nWould you like us to register this number for Mpesa service?\n Yes or No",
                        1: "Confirm registration, by re-entering previous answer"
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
                    "menu_description": "Request lipa na pochi la biashara task",
                    "question_payload": {
                        0: "Lipa pochi!\n\nEnter recipient Mpesa phone number",
                        1: "Confirm number, by repeating it",
                        2: "Enter amount to send"
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
                        1: "Confirm number, by repeating it",
                        2: "Enter amount to send"
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
                        1: "Confirm number, by repeating it",
                        2: "Enter amount to send"
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
                session.add(menu)

            session.commit()
            print("Menu data loaded successfully")

        else:
            print(f"Menu table is not empty, maintaining existing data: {session.query(Menu).all()}")
    except Exception as e:
        print(f"Error occurred while loading menu data: {e}")

# Example usage:
if __name__ == '__main__':
    create_tables()  # Create tables
    load_menu_table()  # Load initial menu data
