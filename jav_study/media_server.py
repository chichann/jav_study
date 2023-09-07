import requests
import json
import yaml
import logging
from .event import event_var

_LOGGER = logging.getLogger(__name__)


class Config:

    def __init__(self):
        self.media_server_name = event_var.media_server_name
        if self.media_server_name:
            config_dir = "/data/conf/base_config.yml"
            with open(config_dir, "r") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
                for config in config["media_server"]:
                    if config["name"] == self.media_server_name:
                        if config["type"] == "emby":
                            self.media_type = 'emby'
                            self.server_url = config["host"]
                            self.port = config["port"]
                            self.https = config["https"]
                            self.base_url = f'https://{self.server_url}:{self.port}' if self.https else f'http://{self.server_url}:{self.port}'
                            self.X_Emby_Token = config["api_key"]
                            self.Limit = 50
                            break
                        elif config["type"] == "plex":
                            self.media_type = 'plex'
                            self.base_url = config["url"]
                            self.token = config["token"]
                            break
                        else:
                            self.media_type = None
                            break
        else:
            self.media_type = None


class EmbyApi:

    def __init__(self):
        self.config = Config()
        self.media_type = self.config.media_type
        if self.media_type == 'emby':
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


class PlexApi:
    from plexapi.server import PlexServer
    def __init__(self):
        self.config = Config()
        self.media_type = self.config.media_type
        if self.media_type == 'plex':
            self.base_url = self.config.base_url
            self.token = self.config.token
            self.server = self.PlexServer(self.base_url, self.token)

    def get_library(self):
        return [library for library in self.server.library.sections()]

    def search_by_keyword(self, keyword):
        movie_libraries = self.get_library()
        for library in movie_libraries:
            results = library.search(keyword)
            if len(results) < 1:
                return False
            elif keyword in results[0].originalTitle:
                return True
        return False
