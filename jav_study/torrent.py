import requests
import logging
from tenacity import retry, stop_after_delay, wait_exponential

from mbot.openapi import mbot_api

from .common import wait_for_mteam, str_cookies_to_dict
from .event import event_var

_LOGGER = logging.getLogger(__name__)
server = mbot_api
site_list = server.site.list()
headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
}


class RetryException(Exception):
    pass


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
    s_list = list(
        filter(lambda x: x.site_id == site_id, site_list))
    if len(s_list) > 0:
        cookie = s_list[0].cookie
        ua = s_list[0].user_agent
        proxy = s_list[0].proxies.strip('/')
        domain = s_list[0].domain.strip('/')
        return cookie, ua, proxy, domain
    else:
        return None


def download_torrent(code, torrent, torrents_folder):
    site_id = torrent["site_id"]
    cookie, ua, proxy, domain = get_site_conf(site_id)
    if ua:
        headers['user-agent'] = ua
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy,
            'socks5': proxy,
        }
    else:
        proxies = None
    cookies = str_cookies_to_dict(cookie)
    try:
        if site_id == 'mteam':
            res = get_mteam_torrent_res(domain, torrent["torrent_id"], headers, cookie, proxies, timeout=30)
        else:
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


@retry(stop=stop_after_delay(300), wait=wait_exponential(multiplier=1, min=30, max=90), reraise=True)
def get_mteam_torrent_res(domain, torrent_id, headers, cookies, proxies, timeout=180):
    try:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        if event_var.mt_apikey:
            headers['x-api-key'] = event_var.mt_apikey
        else:
            headers["Cookie"] = cookies
        payload = f"id={torrent_id}"
        res = requests.post(f"{domain}/api/torrent/genDlToken",
                            headers=headers,
                            proxies=proxies,
                            data=payload,
                            timeout=timeout,
                            allow_redirects=True)
        if res.status_code == 200:
            j = res.json()
            torrent_url = j.get('data')
            if not torrent_url:
                raise RetryException(f'未知错误，错误信息：{j}')
            torrent_content = requests.get(torrent_url,
                                           headers=headers,
                                           proxies=proxies,
                                           timeout=timeout,
                                           allow_redirects=True)
            torrent_content.raise_for_status()
            return torrent_content
        else:
            _LOGGER.error(f"请求下载馒头失败：{res.text}", exc_info=True)
    except Exception as e:
        _LOGGER.error(f'请求种子失败，错误信息：{e}', exc_info=True)
        return None


@retry(stop=stop_after_delay(300), wait=wait_exponential(multiplier=1, min=30, max=90), reraise=True)
def get_torrent_res(site_id, url, headers, cookies, proxies, timeout=180):
    try:
        res = requests.get(url, headers=headers, cookies=cookies, proxies=proxies, timeout=timeout,
                           allow_redirects=True)
        res.raise_for_status()
        if not res.text:
            raise RetryException(f'[{site_id}]未知错误，错误信息：{res.text}')
        if 'application/x-bittorrent' in res.headers.get(
                'Content-Type') or 'application/octet-stream' in res.headers.get('Content-Type'):
            return res
        # if 'google' in res.url:
        #     _LOGGER.error(f'馒头重定向链接到{res.url}。')
        #     _LOGGER.error('遭遇馒头限流，强制等待三到五分钟。')
        #     wait_for_mteam()
        #     raise RetryException(f'遭遇馒头限流，强制等待三到五分钟。')
        if 'Cloudflare' in res.text:
            _LOGGER.error(f'[{site_id}]站点状态当前不可用，请检查可用性。')
            return None
        _LOGGER.error(f'[{site_id}]未知错误，错误信息：{res.text}', exc_info=True)
        return None
    except Exception as e:
        _LOGGER.error(f'[{site_id}]请求种子失败，错误信息：{e}')
        return None
