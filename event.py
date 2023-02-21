from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from typing import Dict, Any
import logging

_LOGGER = logging.getLogger(__name__)


class event_var:

    def __init__(self):
        self.message_to_uid = None
        self.channel = None
        self.proxies = None
        self.headers = None
        self.smms_token = ''
        self.client_name = ''
        self.down_path = ''
        self.jav_list_enable = False
        self.translate_enable = False
        self.appid = ''
        self.sercet = ''


event_var = event_var()


@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    event_var.message_to_uid = config.get('uid')
    event_var.channel = config.get('ToChannelName')
    proxy = config.get('proxy')
    if proxy:
        event_var.proxies = {
            'http': proxy,
            'https': proxy,
            'socks5': proxy,
        }
        _LOGGER.info(f'代理地址：{proxy}')
    else:
        event_var.proxies = None
        _LOGGER.error('请确认你的网络环境能访问JAVLIBRARY，或者设置代理地址')
    user_agent = config.get('user_agent')
    event_var.headers = {
        'User-Agent': user_agent
    }
    event_var.smms_token = config.get('smms_token')
    if not event_var.smms_token:
        _LOGGER.error('请设置smms_token。若不设置，演员订阅推送没有头像')
    event_var.client_name = config.get('client_name')
    event_var.down_path = config.get('down_path')
    event_var.jav_list_enable = config.get('jav_list_enable')
    if event_var.jav_list_enable:
        _LOGGER.info('学习资料自动下载榜单功能已开启')
    event_var.translate_enable = config.get('translate_enable')
    if event_var.translate_enable:
        event_var.appid = config.get('appid')
        event_var.sercet = config.get('sercet')
        _LOGGER.info('学习资料翻译功能已开启')


@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    event_var.message_to_uid = config.get('uid')
    event_var.channel = config.get('ToChannelName')
    proxy = config.get('proxy')
    if proxy:
        event_var.proxies = {
            'http': proxy,
            'https': proxy,
            'socks5': proxy,
        }
        _LOGGER.info(f'代理地址：{proxy}')
    else:
        event_var.proxies = None
        _LOGGER.error('请确认你的网络环境能访问JAVLIBRARY，或者设置代理地址')
    user_agent = config.get('user_agent')
    event_var.headers = {
        'User-Agent': user_agent
    }

    event_var.smms_token = config.get('smms_token')
    if not event_var.smms_token:
        _LOGGER.error('请设置smms_token。若不设置，演员订阅推送没有头像')
    event_var.client_name = config.get('client_name')
    event_var.down_path = config.get('down_path')
    event_var.jav_list_enable = config.get('jav_list_enable')
    if event_var.jav_list_enable:
        _LOGGER.info('学习资料自动下载榜单功能已开启')
    event_var.translate_enable = config.get('translate_enable')
    if event_var.translate_enable:
        event_var.appid = config.get('appid')
        event_var.sercet = config.get('sercet')
        _LOGGER.info('学习资料翻译功能已开启')


