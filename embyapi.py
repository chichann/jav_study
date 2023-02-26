import requests
import json
import yaml
import logging

_LOGGER = logging.getLogger(__name__)


class Config:

    def __init__(self):
        config_dir = "/data/conf/base_config.yml"
        with open(config_dir, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            for config in config["media_server"]:
                if config["type"] == 'emby':
                    self.is_emby = True
                    self.server_url = config["host"]
                    self.port = config["port"]
                    self.https = config["https"]
                    self.base_url = f'https://{self.server_url}:{self.port}' if self.https else f'http://{self.server_url}:{self.port}'
                    self.X_Emby_Token = config["api_key"]
                    self.Limit = 50
                    break
                else:
                    self.is_emby = False
                    self.server_url = None
                    self.port = None
                    self.https = None
                    self.base_url = None
                    self.X_Emby_Token = None
                    self.Limit = None



class EmbyApi:

    def __init__(self):
        self.config = Config()
        self.is_emby = self.config.is_emby
        self.base_url = self.config.base_url
        self.X_Emby_Token = self.config.X_Emby_Token
        self.Limit = self.config.Limit

    def get_emby_user(self):
        url = f'{self.base_url}/emby/Users?X-Emby-Token={self.X_Emby_Token}'
        response = requests.get(url)
        data = json.loads(response.text)
        return data

    def get_emby_item_by_keyword(self, user_id, keyword):
        url = f'{self.base_url}/emby/Users/{user_id}/Items'
        params = {
            'SearchTerm': keyword,
            "X-Emby-Token": self.X_Emby_Token,
            "Limit": self.Limit,
            "Recursive": True
        }
        res = requests.get(url, params=params)
        data = json.loads(res.text)
        return data

    def check_emby_item(self, keyword):
        emby_user_info = self.get_emby_user()
        for user_item in emby_user_info:
            if user_item["Policy"]["IsAdministrator"]:
                user_id = user_item["Id"]
        emby_item = self.get_emby_item_by_keyword(user_id, keyword)
        if len(emby_item["Items"]) < 1:
            return False
        if keyword in emby_item["Items"][0]["Name"]:
            return True

