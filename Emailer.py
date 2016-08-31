
import email.message
import smtplib
import traceback
from config import CONFIG as config

class Emailer():

    def __init__(self):

        self.message = email.message.Message()
        self.message['From'] = config["email"]["address"]
        self.prepare_header(config["email"]["address"])

    def prepare_header(self, to_address):
        self.message['To'] = to_address
        self.message['Subject'] = "Betting results"

    def add_payload(self, notes):
        my_payload = self.get_email_string(notes)

        self.message.set_payload(my_payload)

    def connect(self):
        self.smtpObj = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        self.smtpObj.ehlo()

    def send_email(self, notes):

        self.connect()

        # self.prepare_header(config["email"]["address"])
        self.add_payload(notes)

        try:
            
            self.smtpObj.login(config["email"]["address"], config["email"]["app_pw"])

            try:

                print("Sending email...")

                self.smtpObj.sendmail(config["email"]["address"], config["email"]["address"], 
                    self.message.as_string())

                print("Succesfully sent email")

            except smtplib.SMTPException:
                print("Error: unable to send email")
                traceback.print_exc()

        except:
            print("Error: unable to log in to account")
            traceback.print_exc()

        self.smtpObj.quit()

    def get_email_string(self, notes):
        result = ""

        for game_note in notes:
            result += "{}\n".format(game_note)

        return result