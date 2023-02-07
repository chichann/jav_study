import os
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
import requests
import logging

_LOGGER = logging.getLogger(__name__)
server = mbot_api
site_list = server.site.list()


def get_weight(title, grabs: int, seeders: int, describe):
    cn_keywords = ['中字', '中文字幕', '色花堂', '字幕']
    weight = 0
    content = title + describe
    # 如果seeders和grabs均大于100，权重+100
    if seeders > 100 and grabs > 100:
        weight += 100
    # 如果content中含有中文字幕关键字，权重+1000
    for keyword in cn_keywords:
        if keyword in content:
            weight += 1000
            break
        weight = -1
    # 如果seeders等于0，权重为-1
    if seeders == 0:
        weight = -1
    return weight


def get_best_torrent(torrents):
    if torrents:
        torrents.sort(key=lambda x: x['weight'], reverse=True)
        if torrents[0]['weight'] < 0:
            return None
        return torrents[0]
    return None


def best_torrent_echo(best_torrent: dict):
    if best_torrent:
        title = best_torrent['title']
        size = best_torrent['size']
        describe = best_torrent['describe']
        seeders = best_torrent['seeders']
        caption = f'种子标题：{title}\n' \
                  f'种子描述：{describe}\n' \
                  f'文件大小：{size}\n' \
                  f'做种人数：{seeders}\n'
        pic = best_torrent['img']
        return caption, pic


def get_mteam_conf():
    mt_list = list(
        filter(lambda x: x.site_id == 'mteam', site_list))
    if len(mt_list) > 0:
        cookie = mt_list[0].cookie
        ua = mt_list[0].user_agent
        proxy = mt_list[0].proxies
        domain = mt_list[0].domain
        return cookie, ua, proxy, domain
    else:
        return None


def download_torrent(code, download_url, torrents_folder):
    host = 'https://kp.m-team.cc/'
    cookie, ua, proxy, domain = get_mteam_conf()
    headers = {
        'cookie': cookie,
        'user-agent': ua,
        'Referer': "https://kp.m-team.cc",
    }
    proxies = {
        'http': proxy,
        'https': proxy,
    }
    res = requests.get(host + download_url, headers=headers, proxies=proxies, timeout=30)
    torrent_path = f'{torrents_folder}/{code}.torrent'

    with open(torrent_path, 'wb') as torrent:
        torrent.write(res.content)
        torrent.flush()
    return torrent_path
