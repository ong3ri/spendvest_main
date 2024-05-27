import requests
import os
import base64
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import json
from models import RequestTask, Settlement, Menu, MpesaCustomer, AccountSummary

import random, string 

merchant_code = "600980"


load_dotenv()

def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid

def get_auth_token():
    api_url = 'https://sandbox.sasapay.app/api/v1/auth/token/?grant_type=client_credentials'
    params = {'grant_type' : 'client_credentials'}
    client_id = os.getenv('sasa_client_id')
    client_secret = os.getenv('sasa_client_secret')
    print(f"auth details : {client_id, client_secret}")
    res = requests.get(api_url,
                       auth=HTTPBasicAuth(client_id, client_secret), params=params)
    print(f"response : {res.text}")
    token = res.json()['access_token'] 
    print(f"response for auth token is, {token}")
    return token



def register_callback_url():
    url = "https://sandbox.sasapay.app/api/v1/payments/register-ipn-url/"  # Replace with the actual URL
    
    headers = {
        "key": "Authorization",
        "Authorization": f"Bearer {get_auth_token()} "
    }

    body = {
        "MerchantCode": "600980",  # Replace with the actual merchant code
        "ConfirmationUrl": "https://cb40-102-217-172-2.ngrok-free.app/mpesa_callback"
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        print("Request successful")
        print("Response:", response.json())
    else:
        print("Request failed")
        print("Status code:", response.status_code)
        print("Response:", response.text)
     

def send_user_stk(user_number, amount, menu_code):
    print(f"should be calling stk push")
    url = "https://sandbox.sasapay.app/api/v1/payments/request-payment/"

    headers = {
        "Key": "Authorization",
        "Authorization": f"Bearer {get_auth_token()}"
    }

    body = {
        "MerchantCode": "600980",
        "NetworkCode": "63902",
        "PhoneNumber":user_number,
        "TransactionDesc": "Deposit for Service",
        "AccountReference": generate_uid(10),
        "Currency": "KES",
        "Amount": amount,
        "TransactionFee": 0,
        "CallBackURL": "https://d7d7-102-217-172-2.ngrok-free.app/mpesa_callback"
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        print("Request successful")
        customer_message = response.json()['CustomerMessage']
        print("Response for customer message:", customer_message)
        # call request task
        service_description = Menu.get_menu(menu_code)
        if service_description != False:
            description = service_description['menu_description']
            RequestTask.add_request_task(user_number, menu_code, description, body)
            Settlement.add_settlement(user_number,menu_code, amount, False)
            summary = AccountSummary.get_acc_summary(user_number)

            AccountSummary.update_acc_summary(user_number, {
                'total_deposit':int(summary[b'total_deposit'].decode('utf-8')) + 1,
                'total_settlement':int(summary[b'total_settlement'].decode('utf-8')) + 1,
                'amount_deposited':float(summary[b'amount_deposited'].decode('utf-8')) + amount
            })

            return customer_message

    else:
        print("Request failed")
        print("Status code:", response.status_code)
        print("Response:", response.text) 


def send_payment(receiving_number, send_amount):
    url = "https://sandbox.sasapay.app/api/v1/payments/b2c/"  # Replace with the actual URL

    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Key": "Authorization"
    }

    body = {
    "MerchantCode": "600980",
    "MerchantTransactionReference": f"{generate_uid()}",
    "Currency": "KES",
    "Amount": str(send_amount),
    "ReceiverNumber": str(receiving_number),
    "Channel": "63902",
    "CallBackURL": "https://d7d7-102-217-172-2.ngrok-free.app/mpesa_callback",
    "Reason": "Test B2C"
    }

    print(f"sending body is : {body}")
    
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code == 200:
        print("Request was successful.")
        print("Response:", response.json())
        # update the settlement completed

    else:
        print("Request failed with status code:", response.status_code)
        print("Response:", response.text)



def get_acc_balance():
    url = f"https://sandbox.sasapay.app/api/v1/payments/check-balance/?MerchantCode={merchant_code}"  # Replace with the actual balance endpoint URL
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "key": "Authorization"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Successfully received a response
        balance_data = response.json()
        return balance_data['data']['Accounts']
    else:
        # Handle errors
        print(f"Failed to get balance. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None 