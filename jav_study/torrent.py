from mbot.openapi import mbot_api
import requests
import logging
from .common import wait_for_mteam, str_cookies_to_dict
from .event import event_var

_LOGGER = logging.getLogger(__name__)
server = mbot_api
site_list = server.site.list()


def get_weight(torrent_rank, min_size, max_size):
    cn_keywords = ['中字', '中文字幕', '色花堂', '字幕', '98堂']
    weight = 0
    name = torrent_rank["name"]
    subject = torrent_rank["subject"]
    upload_count = torrent_rank["upload_count"]
    download_count = torrent_rank["download_count"]
    content = name + subject
    _LOGGER.info(f'[{torrent_rank["site_id"]}]: {content}|upload_count:{upload_count}|download_count:{download_count}')
    if upload_count > 10 and download_count > 30:
        weight += 100
    # 如果content中含有中文字幕关键字，权重+1000
    for keyword in cn_keywords:
        if keyword in content:
            weight += 1000
            break
    # 如果做种人数等于0，权重为-1
    if upload_count == 0:
        _LOGGER.info(f'[{torrent_rank["site_id"]}]: {content}|做种人数为0,跳过')
        weight = -1
    # 如果文件限制值为0，则表示无限制,跳过以下判断
    if min_size == 0 and max_size == 0:
        _LOGGER.info(f'[{torrent_rank["site_id"]}]: {content}|最终权重为{weight}')
        return weight
    # 如果文件大小超过限制，权重为-1
    size = torrent_rank["size"]
    if 'MB' in size:
        size_gb = float(size.split('MB')[0]) / 1024
    elif 'GB' in size:
        size_gb = float(size.split('GB')[0])
    if size_gb < float(min_size) or size_gb > float(max_size):
        _LOGGER.info(f'[{torrent_rank["site_id"]}]: {content}|文件大小{size}不在限制范围内')
        weight = -1
    _LOGGER.info(f'[{torrent_rank["site_id"]}]: {content}|最终权重为{weight}')
    return weight


def get_best_torrent(torrents):
    weight = 999 if event_var.chs_enable else 0
    if not torrents:
        return None
    torrents.sort(key=lambda x: x['weight'], reverse=True)
    if torrents[0]['weight'] > weight:
        return torrents[0]
    if weight == 0 and torrents[0]['weight'] > -1:
        torrents = [torrent for torrent in torrents if torrent['weight'] != -1]
        torrents.sort(key=lambda x: x['upload_count'], reverse=True)
        return torrents[0]
    return None


def best_torrent_echo(best_torrent: dict):
    if best_torrent:
        name = best_torrent['name']
        subject = best_torrent['subject']
        site_id = best_torrent['site_id']
        size = best_torrent['size']
        upload_count = best_torrent['upload_count']
        caption = f'种子标题：{name}\n' \
                  f'种子描述：{subject}\n' \
                  f'站点：{site_id}\n' \
                  f'文件大小：{size}\n' \
                  f'做种人数：{upload_count}\n'
        poster_url = best_torrent['poster_url']
        return caption, poster_url


def get_site_conf(site_id):
    mt_list = list(
        filter(lambda x: x.site_id == site_id, site_list))
    if len(mt_list) > 0:
        cookie = mt_list[0].cookie
        ua = mt_list[0].user_agent
        proxy = mt_list[0].proxies
        domain = mt_list[0].domain
        return cookie, ua, proxy, domain
    else:
        return None


def download_torrent(code, torrent, torrents_folder):
    site_id = torrent["site_id"]
    cookie, ua, proxy, domain = get_site_conf(site_id)
    headers = {
        'cookie': cookie,
        'user-agent': ua,
    }
    proxies = {
        'http': proxy,
        'https': proxy,
        'socks5': proxy,
    }
    cookies = str_cookies_to_dict(cookie)
    try:
        res = get_torrent_res(site_id, torrent["download_url"], headers, cookies, proxies, timeout=30)
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f'[{site_id}]请求失败：{str(e)}')
        return None
    if res is None:
        return None
    torrent_path = f'{torrents_folder}/[{site_id}]{code}.torrent'
    try:
        with open(torrent_path, 'wb') as torrent:
            torrent.write(res.content)
            torrent.flush()
        return torrent_path
    except Exception as e:
        logging.error(f'[{site_id}]写入种子文件失败：{str(e)}', exc_info=True)
        return None


def get_torrent_res(site_id, url, headers, cookies, proxies, timeout=30):
    try:
        for i in range(3):
            res = requests.get(url, headers=headers, cookies=cookies, proxies=proxies, timeout=timeout)
            if 'application/x-bittorrent' in res.headers.get('Content-Type'):
                return res
            if 'google' in res.url:
                _LOGGER.error(f'馒头重定向链接到{res.url}。')
                _LOGGER.error('遭遇馒头限流，强制等待三到五分钟。')
                wait_for_mteam()
                continue
            if 'Cloudflare' in res.text:
                _LOGGER.error(f'[{site_id}]站点状态当前不可用，请检查可用性。')
                return None
    except Exception as e:
        _LOGGER.error(f'请求种子失败，错误信息：{e}')
        return None
