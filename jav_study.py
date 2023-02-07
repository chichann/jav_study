import os.path
import time

from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from flask import Blueprint, request
from mbot.common.flaskutils import api_result
from .translate import *
from .download_client import *
from .torrent import *

from typing import Dict, Any
import requests
from bs4 import BeautifulSoup, SoupStrainer
import logging

server = mbot_api
_LOGGER = logging.getLogger(__name__)
torrent_folder = '/data/plugins/jav_study/torrents'
bp = Blueprint('jav_study', __name__)
"""
把flask blueprint注册到容器
这个URL访问完整的前缀是 /api/plugins/你设置的前缀
"""
plugin.register_blueprint('jav_study', bp)


@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global message_to_uid, channel, proxies, headers, client_name, down_path, appid, sercet, translate_enable
    message_to_uid = config.get('uid')
    channel = config.get('ToChannelName')
    proxy = config.get('proxy')
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy,
        }
        _LOGGER.info(f'代理地址：{proxy}')
    else:
        _LOGGER.error('请确认你的网络环境能访问JAVLIBRARY，或者设置代理地址')
    user_agent = config.get('user_agent')
    headers = {
        'User-Agent': user_agent,
    }
    client_name = config.get('client_name')
    # category = config.get('category')
    down_path = config.get('down_path')
    translate_enable = config.get('translate_enable')
    if translate_enable:
        appid = config.get('appid')
        sercet = config.get('sercet')
        _LOGGER.info('JAV翻译功能已开启')


@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global message_to_uid, channel, proxies, headers, client_name, down_path, appid, sercet, translate_enable
    message_to_uid = config.get('uid')
    channel = config.get('ToChannelName')
    proxy = config.get('proxy')
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy,
        }
        _LOGGER.info(f'代理地址：{proxy}')
    else:
        _LOGGER.error('请确认你的网络环境能访问JAVLIBRARY，或者设置代理地址')
    user_agent = config.get('user_agent')
    headers = {
        'User-Agent': user_agent,
    }
    client_name = config.get('client_name')
    # category = config.get('category')
    down_path = config.get('down_path')
    translate_enable = config.get('translate_enable')
    if translate_enable:
        appid = config.get('appid')
        sercet = config.get('sercet')
        _LOGGER.info('JAV翻译功能已开启')


@plugin.task('jav_list_task', '定时爬取JAV影片榜单', cron_expression='34 23 * * *')
def jav_list_task():
    run_and_download_list()


def like_list_judge(like_list):
    code_list, exist_list = [], []
    for item in like_list:
        code_list.append(item['av_id'])
    downloaded_code = get_cache(sign='downloaded_code')
    un_download_code = get_cache(sign='un_download_code')
    if downloaded_code is not None:
        exist_list.extend(downloaded_code)
    if un_download_code is not None:
        exist_list.extend(un_download_code)
    if exist_list is not None:
        return [code for code in code_list if code not in exist_list]
    else:
        return code_list


def run_and_download_list():
    result = get_jav_like()
    try:
        if result:
            code_list = like_list_judge(result)
            if len(code_list) > 0:
                _LOGGER.info(f'JAV最受欢迎影片本次新增{"、".join(code_list)},共{len(code_list)}部')
            if code_list:
                for code in code_list:
                    _LOGGER.info(f'番号「{code}」提交搜索')
                    sub_result, flag = torrent_main(code)
                    if flag == 0:
                        _LOGGER.error(f'JAV最受欢迎影片{sub_result}')
                        add_un_download_list(code)
                        time.sleep(30)
                        continue
                    elif flag == 1:
                        _LOGGER.info(f'JAV最受欢迎影片{sub_result}')
                        time.sleep(30)
                        continue
                    else:
                        _LOGGER.error(f'JAV最受欢迎影片{sub_result}')
                        time.sleep(30)
                        continue
                _LOGGER.info('JAV最受欢迎影片本次新增影片搜索完成')
            else:
                _LOGGER.error('JAV最受欢迎影片无更新新片')
                return True
        else:
            return False
    except Exception as e:
        logging.error(f'JAV最受欢迎影片获取失败，错误信息：{e}', exc_info=True)
        return False


@plugin.task('un_download_code_research_task', '未下载列表重新搜索资源', cron_expression='12 23 * * *')
def un_download_code_research_task():
    un_download_code = get_cache(sign='un_download_code')
    downloaded_code_now = []
    if not un_download_code:
        _LOGGER.info('未下载列表为空')
        return
    for code in un_download_code:
        search_result, flag = torrent_main(code)
        if flag == 0:
            _LOGGER.info(f'「{code}」重新搜索未找到资源，等待下次重试。')
        elif flag == 1:
            downloaded_code_now.append(code)
        time.sleep(60)
    if downloaded_code_now:
        for item in downloaded_code_now:
            un_download_code.remove(item)
        set_cache(sign='un_download_code', code_list=un_download_code)


def jav_list_echo(result):
    caption_list, img_list = [], []
    if result:
        for item in result:
            av_id = f'番号：{item["av_id"]}\n'
            av_title = f'标题：{item["av_title"]}\n'
            av_date = f'发行日期：{item["av_date"]}\n'
            av_actor = f'演员：{item["av_actor"]}\n' if item['av_actor'] else '演员：素人\n'
            av_genre = f'类型：{item["av_genre"]}\n'
            av_img = item['av_img']
            caption = f'{av_id}{av_title}{av_actor}{av_date}{av_genre}'
            caption_list.append(caption)
            img_list.append(av_img)
        return caption_list, img_list


@bp.route('/search', methods=["GET"])
def search():
    keyword = request.args.get('keyword') if request.args.get('keyword') else ''
    if keyword:
        search_result_json: list = jav_search(keyword)
        if search_result_json is not None:
            return api_result(code=0, message='查询成功', data=search_result_json)
        else:
            return api_result(code=1, message='查询失败,请查看日志', data='')
    else:
        return api_result(code=1, message='请输入关键字', data='')


@bp.route('/list', methods=["GET"])
def like_list():
    result: list = get_jav_like()
    send = request.args.get('send_notify') if request.args.get('send_notify') else ''
    if result:
        if send == 'true':
            caption, pic = jav_list_echo(result)
            title = '今日JAV最受欢迎影片\n'
            send_notify(title, caption, pic)
            _LOGGER.info(f'查询成功，通知已发送')
            return api_result(code=0, message='查询成功，通知已发送', data=result)
        _LOGGER.info(f'查询成功')
        return api_result(code=0, message='查询成功', data=result)
    else:
        return api_result(code=1, message='查询失败,请查看日志', data='')


@bp.route('/sub', methods=["GET"])
def sub():
    code = request.args.get('code') if request.args.get('code') else ''
    if code:
        sub_result, flag = torrent_main(code)
        if flag == 1:
            return api_result(code=0, message='订阅成功', data=sub_result)
        else:
            add_un_download_list(code)
            return api_result(code=1, message='订阅失败,请查看日志', data=sub_result)
    else:
        return api_result(code=1, message='请输入番号', data='')


def get_jav_like():
    url = 'https://www.javlibrary.com/cn/vl_mostwanted.php?page=1'
    # result_list = []
    try:
        _LOGGER.info(f'开始获取JAV最受欢迎影片')
        r = requests.get(url=url, headers=headers, proxies=proxies, timeout=30)
        list_select = 'div.videos > div.video'
        soup_tmp = SoupStrainer('div', {'class': 'videos'})
        soup = BeautifulSoup(r.text, 'html.parser', parse_only=soup_tmp)
        av_list = soup.select(list_select)
        result_list = jav_list_result(av_list)
        if result_list:
            return result_list
        else:
            return False
    except Exception as e:
        logging.error(f'获取JAV最受欢迎影片失败，原因为{e}', exc_info=True)
        return False


def jav_search(keyword):
    code = set_true_code(keyword)
    url = f'https://www.javlibrary.com/cn/vl_searchbyid.php?keyword={code}'
    result_list = []
    try:
        _LOGGER.info(f'开始在javlibrary查询「{code}」')
        r = requests.get(url=url, headers=headers, proxies=proxies, timeout=30)
        list_select = 'div.videos > div.video'
        soup_tmp = SoupStrainer('div', {'class': 'videos'})
        soup = BeautifulSoup(r.text, 'html.parser', parse_only=soup_tmp)
        av_list = soup.select(list_select)
        if av_list:
            result_list = jav_list_result(av_list)
        else:
            soup2_tmp = SoupStrainer('div', {'id': 'rightcolumn'})
            soup2 = BeautifulSoup(r.text, 'html.parser', parse_only=soup2_tmp)
            video_info = get_detail(soup2)
            if video_info:
                result_list.append(video_info)
            else:
                result_list = None
        if result_list is not None:
            _LOGGER.info(f'查询「{code}」成功，结果：{result_list}')
            return result_list
        else:
            _LOGGER.error(f'查询「{code}」失败，找不到结果')
            return None
    except Exception as e:
        logging.error(f'查询「{code}」失败，原因为{e}', exc_info=True)
        return None


def jav_list_result(av_list):
    result_list = []
    try:
        for av in av_list:
            av_href = av.select('a')[0].get('href')
            av_href = 'https://www.javlibrary.com/cn' + av_href.strip('.')
            r = requests.get(url=av_href, headers=headers, proxies=proxies, timeout=30)
            soup_tmp = SoupStrainer('div', {'id': 'rightcolumn'})
            soup = BeautifulSoup(r.text, 'html.parser', parse_only=soup_tmp)
            video_info = get_detail(soup)
            result_list.append(video_info)
        return result_list
    except Exception as e:
        logging.error(f'javlibrary搜索列表解析失败，原因为{e}', exc_info=True)
        return False


def get_detail(soup):
    video_info = {}
    try:
        if '搜寻没有结果' in soup.text:
            _LOGGER.error(f'javlibrary搜索列表解析失败，找不到任何结果')
            return None
        else:
            av_id = soup.select('div#video_title > h3 > a')[0].contents[0].split(' ', 1)[0]
            av_title = soup.select('div#video_title > h3 > a')[0].contents[0].split(' ', 1)[1]
            if translate_enable:
                av_title_translated = trans_main(av_title, appid, sercet)
                if av_title_translated:
                    av_title = av_title_translated
            video_date = soup.select('div#video_date > table > tr > td.text')[0].contents[0]
            genres = soup.select('div#video_genres > table > tr > td.text > span.genre > a')
            genre = ''
            for i in genres:
                genre += i.contents[0] + ' / '
            actor_select = 'div#video_cast > table > tr > td.text > span > span.star > a'
            actors = soup.select(actor_select)
            actor = ''
            for i in actors:
                actor += i.contents[0] + ' / '
            av_img = soup.select('img#video_jacket_img')[0].get('src')
            video_info['av_id'] = av_id
            video_info['av_title'] = av_title
            video_info['av_actor'] = actor.rstrip(' / ')
            video_info['av_date'] = video_date
            video_info['av_genre'] = genre.rstrip(' / ')
            video_info['av_img'] = 'https:' + av_img
            return video_info
    except Exception as e:
        logging.error(f'javlibrary详情页解析失败，原因为{e}', exc_info=True)
        return None


def send_notify(title, content, pic):
    channel_table = channel.split(',') if channel else None
    for channel_item in channel_table:
        if message_to_uid:
            for _ in message_to_uid:
                server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                    'title': title,
                    'a': content,
                    'pic_url': pic
                }, to_uid=_, to_channel_name=channel_item)
        else:
            server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                'title': title,
                'a': content,
                'pic_url': pic
            }, to_channel_name=channel_item)


def get_cache(sign):
    cache_list = server.common.get_cache('jav_search', sign)
    return cache_list


def set_cache(sign, code_list):
    try:
        server.common.set_cache('jav_search', sign, code_list)
        return True
    except Exception as e:
        logging.error(f'jav_search写入缓存失败，错误信息：{e}')
        return False


def add_un_download_list(code):
    un_download_code = get_cache(sign='un_download_code')
    if un_download_code:
        if code in un_download_code:
            _LOGGER.info(f'「{code}」已存在于未下载列表')
            return False
        un_download_code.append(code)
    else:
        un_download_code = [code]
    if set_cache(sign='un_download_code', code_list=un_download_code):
        _LOGGER.info(f'「{code}」已添加到未下载列表，等待下次重试。')
        caption, pic = jav_list_echo(jav_search(code))
        send_notify(title='有新的学习资料添加到未下载列表\n',
                    content=caption[0],
                    pic=pic[0])
        return True


def add_download_list(code):
    downloaded_code = get_cache(sign='downloaded_code')
    if downloaded_code:
        downloaded_code.append(code)
    else:
        downloaded_code = [code]
    if set_cache(sign='downloaded_code', code_list=downloaded_code):
        _LOGGER.info(f'「{code}」已添加到已下载列表，不会再重复下载。')
        return True


def set_true_code(code):
    code_list = code.split('-')
    code = ''.join(code_list).replace('\r', '').replace('\n', '')
    length = len(code)
    index = length - 1
    num = ''
    all_number = '0123456789'
    while index > -1:
        s = code[index]
        if s not in all_number:
            break
        num = s + num
        index -= 1
    prefix = code[0:index + 1]
    return (prefix + '-' + num).upper()


def torrent_main(keyword):
    code = set_true_code(keyword)
    downloaded_code = get_cache(sign='downloaded_code')
    if downloaded_code:
        if code in downloaded_code:
            _LOGGER.info(f'「{code}」已下载过')
            flag = 2
            return f'「{code}」已下载过', flag
    torrents = search_mteam(code)
    if torrents:
        best_torrent = get_best_torrent(torrents)
        if best_torrent:
            _LOGGER.info(f'找到最佳种子：标题：{best_torrent["title"]}，下载地址：{best_torrent["download_url"]}')
            torrent_path = download_torrent(code, best_torrent['download_url'], torrent_folder)
            if torrent_path:
                _LOGGER.info(f'「{code}」种子下载成功')
            else:
                _LOGGER.error(f'「{code}」种子下载失败，下载地址：{best_torrent["download_url"]}')
                flag = 0
                return f'「{code}」种子下载失败，请检查站点连通性，下载地址：{best_torrent["download_url"]}', flag
            caption, pic = best_torrent_echo(best_torrent)
            res = download(torrent_path=torrent_path, save_path=down_path, category=None, client_name=client_name)
            if res:
                _LOGGER.info(f'「{code}」提交下载成功')
                title = f'「{code}」提交下载成功\n'
                send_notify(title, caption, pic)
                add_download_list(code)
                flag = 1
                return best_torrent, flag
            else:
                _LOGGER.info(f'「{code}」提交下载失败')
                title = f'「{code}」提交下载失败\n'
                send_notify(title, caption, pic)
                flag = 2
                return f'「{code}」提交下载失败，可能是下载器已存在该种子。请检查QB，并且该种子不会自动重试。', flag
        else:
            _LOGGER.error(f'「{code}」没有找到合适的种子')
            flag = 0
            return f'「{code}」没有找到合适的种子', flag
    else:
        _LOGGER.error(f'「{code}」没有找到任何资源')
        flag = 0
        return f'「{code}」没有找到任何资源', flag
