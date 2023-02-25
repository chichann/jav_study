from mbot.openapi import mbot_api
import requests
import logging
from .common import wait_for_mteam

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
    # 如果做种人数和下载完成人数都超过50，权重+100
    if upload_count > 50 and download_count > 50:
        weight += 100
    # 如果content中含有中文字幕关键字，权重+1000
    for keyword in cn_keywords:
        if keyword in content:
            weight += 1000
            break
    # 如果做种人数等于0，权重为-1
    if upload_count == 0:
        weight = -1
    # 如果文件限制值为0，则表示无限制,跳过以下判断
    if min_size == 0 and max_size == 0:
        return weight
    # 如果文件大小超过限制，权重为-1
    size = torrent_rank["size"]
    if 'MB' in size:
        size = float(size.split('MB')[0]) / 1024
    elif 'GB' in size:
        size = float(size.split('GB')[0])
    if size < float(min_size) or size > float(max_size):
        weight = -1
    _LOGGER.info(f'[{torrent_rank["site_id"]}]: {content}|最终权重为{weight}')
    return weight


def get_best_torrent(torrents):
    if torrents:
        torrents.sort(key=lambda x: x['weight'], reverse=True)
        if torrents[0]['weight'] <= 0:
            return None
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
    res = get_torrent_res(torrent["download_url"], headers, proxies, timeout=30)
    if 'cloudflare' in res.text:
        _LOGGER.error(f'「{site_id}」站点状态当前不可用，请检查可用性。')
        return None
    torrent_path = f'{torrents_folder}/{code}.torrent'

    with open(torrent_path, 'wb') as torrent:
        torrent.write(res.content)
        torrent.flush()
    return torrent_path


def get_torrent_res(url, headers, proxies, timeout=30):
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
        if 'google' in res.text:
            _LOGGER.error('可能遭遇馒头限流，强制等待三分钟。')
            wait_for_mteam()
            return get_torrent_res(url, headers, proxies, timeout)
        return res
    except Exception as e:
        _LOGGER.error(f'请求失败，错误信息：{e}')
        return None
