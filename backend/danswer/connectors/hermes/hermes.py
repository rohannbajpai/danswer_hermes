import requests
import datetime

HERMES_URL = "https://hermesapp.net/api/"

class Hermes:
    """ Handles interactions with Hermes API """
    def __init__(
        self, access_token: str | None = None
    ) -> None:
        self.access_token = access_token

    def get_all_message_threads(self):
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        body = {
            "datetime": str(datetime.datetime.now(datetime.timezone.utc))
        }
        response = requests.post(url = f"{HERMES_URL}get_threads", headers=headers, json=body)
        
        return response.json()
    
    def get_all_spaces(self):
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        body = {
            "datetime": str(datetime.datetime.now(datetime.timezone.utc))
        }
        response = requests.post(url = f"{HERMES_URL}get_spaces", headers=headers, json=body)
        print(response.text)
        return response.json()