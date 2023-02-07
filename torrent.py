import os
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from bs4 import BeautifulSoup, SoupStrainer
import requests
import logging
from .jav_study import *
_LOGGER = logging.getLogger(__name__)
server = mbot_api
site_list = server.site.list()


def search_mteam(keyword):
    cookie, ua, proxy, domain = get_mteam_conf()
    url = f'https://kp.m-team.cc/adult.php?incldead=1&spstate=0&inclbookmarked=0&search={keyword}&search_area=0&search_mode=0'
    headers = {
        'cookie': cookie,
        'user-agent': ua,
        'Referer': "https://kp.m-team.cc",
    }
    proxies = {
        'http': proxy,
        'https': proxy,
    }
    dict_cookie = str_cookies_to_dict(cookie)
    response = requests.get(url, headers=headers, cookies=dict_cookie, proxies=proxies, timeout=30).text
    if 'cloudflare' in response:
        _LOGGER.error('可能遭遇CloudFlare五秒盾，一会再试试吧。')
        return False
    soup_tmp = SoupStrainer('table', {'class': 'torrents'})
    soup = BeautifulSoup(response, 'html.parser', parse_only=soup_tmp)
    trs = soup.select('table.torrents > tr:has(table.torrentname)')
    torrents = []
    for tr in trs:
        title = tr.select('a[title][href^="details.php?id="]')[0].get('title')
        download_url = tr.select('a[href^="download.php?id="]')[0].get('href')
        size = tr.select('td.rowfollow:nth-last-child(6)')[0].text
        seeders = tr.select('td.rowfollow:nth-last-child(5)')[0].text.replace(',', '')
        leechers = tr.select('td.rowfollow:nth-last-child(4)')[0].text.replace(',', '')
        grabs = tr.select('td.rowfollow:nth-last-child(3)')[0].text.replace(',', '')
        describe_list = tr.select('table.torrentname > tr > td.embedded')[0].contents
        describe = describe_list[len(describe_list) - 1].text
        img = tr.select('img[alt="torrent thumbnail"]')[0].get('src')
        torrent_rank = {
            'title': title,
            'download_url': download_url,
            'size': size,
            'seeders': seeders,
            'leechers': leechers,
            'grabs': grabs,
            'describe': describe,
            'img': img,
        }
        weight = get_weight(title, int(grabs), int(seeders), describe)
        torrent_rank['weight'] = weight
        torrents.append(torrent_rank)
    return torrents


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


def str_cookies_to_dict(cookies):
    dict_cookie = {}
    str_cookie_list = cookies.split(';')
    for cookie in str_cookie_list:
        if cookie.strip(' '):
            cookie_key_value = cookie.split('=')
            if len(cookie_key_value) < 2:
                continue
            key = cookie_key_value[0]
            value = cookie_key_value[1]
            dict_cookie[key] = value
    return dict_cookie



