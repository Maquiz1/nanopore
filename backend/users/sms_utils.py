import africastalking
import random
import os

username = os.getenv("AT_USERNAME")
api_key = os.getenv("AT_API_KEY")

africastalking.initialize(username, api_key)
sms = africastalking.SMS

def send_verification_sms(phone_number):
    code = str(random.randint(100000, 999999))
    message = f"Your verification code is: {code}"
    try:
        response = sms.send(message, [phone_number])
        print(f"SMS send response: {response}")
        return code
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return None
