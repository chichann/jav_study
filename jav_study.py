import json

from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from mbot.common.flaskutils import api_result

from flask import Blueprint, request
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup, SoupStrainer
import logging
import os.path
import time

from .event import event_var
from .download_client import download
from .torrent import get_best_torrent, best_torrent_echo, download_torrent
from .common import get_cache, set_cache, add_un_download_list, add_download_list, send_notify
from .crawl import jav_crawl, mteam_crawl, javbus_crawl

server = mbot_api
_LOGGER = logging.getLogger(__name__)
torrent_folder = '/data/plugins/jav_study/torrents'
if not os.path.exists(torrent_folder):
    os.makedirs(torrent_folder)


@plugin.task('jav_list_task', '定时爬取JAV影片榜单', cron_expression='34 */6 * * *')
def jav_list_task():
    run_and_download_list()


@plugin.task('un_download_code_research_task', 'JAV番号订阅重新搜索', cron_expression='16 7,17 * * *')
def un_download_code_research_task():
    un_download_research()


@plugin.task('research_star_sub', 'JAV演员订阅重新搜索', cron_expression='15 8,18 * * *')
def research_star_sub_task():
    search_code_by_star_record()
    run_sub_star_record()


def un_download_research():
    un_download_code = get_cache(sign='un_download_code')
    downloaded_code_now = []
    if not un_download_code:
        _LOGGER.info('未下载列表为空')
        return
    _LOGGER.info(f'开始重新搜索未下载列表中的番号：{",".join(un_download_code)}')
    for code in un_download_code:
        code_sub_result = torrent_main(code)
        if code_sub_result["flag"] == 0:
            _LOGGER.info(f'「{code}」重新搜索未找到资源，等待下次重试。')
        elif code_sub_result["flag"] == 1:
            downloaded_code_now.append(code)
        time.sleep(30)
    if downloaded_code_now:
        for item in downloaded_code_now:
            un_download_code.remove(item)
        set_cache(sign='un_download_code', value=un_download_code)


def search_list_judge_recorded(code_list_before):
    code_list, exist_list = [], []
    for item in code_list_before:
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


def get_sub_code_list():
    un_download_code = get_cache(sign='un_download_code')
    if un_download_code:
        # 把列表un_download_code中的每个值转成字典格式,参数有name和value
        sub_list = [{'name': code, 'value': code} for code in un_download_code]
        return sub_list


def delete_code_sub(code):
    _LOGGER.info(f'开始删除订阅「{code}」')
    code = ''.join(code)
    un_download_code = get_cache(sign='un_download_code')
    if un_download_code:
        if code in un_download_code:
            un_download_code.remove(code)
            _LOGGER.info(f'删除订阅「{code}」成功')
            set_cache(sign='un_download_code', value=un_download_code)
            return True
        else:
            return False


def get_sub_star_list():
    sub_star = get_cache(sign='actor_sub')
    sub_star_list = []
    if sub_star:
        for item in sub_star:
            name = item['star_name']
            date = item['monitor_date']
            sub_star_list.append({'name': f'{name} | {date}', 'value': name})
        return sub_star_list


def delete_star_sub(star_name):
    _LOGGER.info(f'开始删除订阅「{star_name}」')
    star_name = ''.join(star_name)
    sub_star = get_cache(sign='actor_sub')
    if sub_star:
        for item in sub_star:
            if item['star_name'] == star_name:
                del_url = item['del_avatar_img']
                del_avatar_img(del_url)
                sub_star.remove(item)
                _LOGGER.info(f'删除订阅「{star_name}」成功')
                set_cache(sign='actor_sub', value=sub_star)
                set_cache(sign=star_name, value=[])
                return True


def del_avatar_img(url):
    if url:
        r = requests.get(url, proxies=event_var.proxies, timeout=10)
        if r.status_code == 200:
            return True


def run_and_download_list():
    result = jav_crawl().get_jav_like()
    try:
        if result:
            code_list = search_list_judge_recorded(result)
            if len(code_list) > 0:
                _LOGGER.info(f'JAV最受欢迎影片本次新增{"、".join(code_list)},共{len(code_list)}部')
            if code_list:
                for code in code_list:
                    _LOGGER.info(f'番号「{code}」提交搜索')
                    code_sub_result = torrent_main(code)
                    if code_sub_result["flag"] == 0:
                        _LOGGER.error(f'JAV最受欢迎影片{code_sub_result["sub_result"]}')
                        add_un_download_list(code)
                        time.sleep(30)
                        continue
                    elif code_sub_result["flag"] == 1:
                        _LOGGER.info(f'JAV最受欢迎影片{code_sub_result["sub_result"]}')
                        time.sleep(30)
                        continue
                    else:
                        _LOGGER.error(f'JAV最受欢迎影片{code_sub_result["sub_result"]}')
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


def sub_by_star(star, date):
    import datetime
    date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    actor_sub = get_cache(sign="actor_sub")
    update_result = update_monitor_date(star, date)
    if not update_result.get("flag"):
        star_info = javbus_crawl().crawl_star_code(star)
        if not star_info:
            _LOGGER.error(f'「{star}」演员信息获取失败,请检查演员名是否正确')
            return None
        star_info["monitor_date"] = date
        _LOGGER.info(f'「{star}」演员信息获取成功')
        if not actor_sub:
            actor_sub = [star_info]
            star_info["movie_list"] = []
            msg = '订阅成功'
        else:
            if star_info["star_id"] not in [x["star_id"] for x in actor_sub]:
                actor_sub.append(star_info)
                star_info["movie_list"] = []
                msg = '订阅成功'
            else:
                msg = '已订阅过，更新监控日期成功'
        set_cache(sign=star_info["star_name"], value=star_info)
        set_cache(sign='actor_sub', value=actor_sub)
    else:
        msg = '已订阅过，更新监控日期成功'
        star_info = update_result.get("star_info")
    title = f'「{star_info["star_name"]}」{msg}\n'
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    caption = ''
    if star_info["star_detail"]:
        for item in star_info["star_detail"]:
            caption += item + '\n'
    caption += f'\n订阅时间：{now}\n'
    caption += f'开始监控{star_info["monitor_date"]}之后的影片'
    pic = star_info['star_avatar']
    send_notify(title, caption, pic)
    _LOGGER.info(f'「{star_info["star_name"]}」{msg}')
    _LOGGER.info(f'开始监控{star_info["monitor_date"]}之后的影片')
    search_code_by_single_star(star_info)
    single_star_info = get_cache(sign=star_info["star_name"])
    run_sub_single_star_code(single_star_info)
    return True


def update_monitor_date(star, date):
    actor_sub = get_cache(sign='actor_sub')
    if actor_sub:
        for star_info in actor_sub:
            if star_info["star_name"] == star:
                star_info["monitor_date"] = date
                set_cache(sign='actor_sub', value=actor_sub)
                return {'flag': True, 'star_info': star_info}
    return {'flag': False}


def single_codee_judge_record(code):
    exist_list = []
    downloaded_code = get_cache(sign='downloaded_code')
    un_download_code = get_cache(sign='un_download_code')
    if downloaded_code is not None:
        exist_list.extend(downloaded_code)
    if un_download_code is not None:
        exist_list.extend(un_download_code)
    return code if exist_list is None or code not in exist_list else None


def search_code_by_star_record():
    actor_sub = get_cache(sign='actor_sub')
    if actor_sub:
        for star_info in actor_sub:
            search_code_by_single_star(star_info)
    else:
        _LOGGER.info('未发现订阅的老师')


def search_code_by_single_star(star_info):
    movie_list = javbus_crawl().crawl_list_by_star(star_info["star_id"])
    star_info = get_cache(sign=star_info["star_name"])
    if movie_list:
        if not star_info["movie_list"]:
            star_info["movie_list"] = movie_list
        else:
            for movie in movie_list:
                # 判断movie_list中每一项是否在item['movie_list']中已存在，如果存在则跳过，不存在则添加
                if movie["movie_code"] not in [x["movie_code"] for x in star_info["movie_list"]]:
                    star_info["movie_list"].append(movie)
    for movie in star_info["movie_list"]:
        if movie["status"] == 0:
            judge = single_codee_judge_record(movie["movie_code"])
            if not judge:
                movie["status"] = 1
            continue
    set_cache(sign=star_info["star_name"], value=star_info)
    _LOGGER.info(f'「{star_info["star_name"]}」影片同步数据完成')


def run_sub_star_record():
    actor_sub = get_cache(sign='actor_sub')
    if actor_sub:
        for star_info in actor_sub:
            single_star_info = get_cache(sign=star_info['star_name'])
            run_sub_single_star_code(single_star_info)
        _LOGGER.info('订阅的老师影片搜索完成')
    else:
        _LOGGER.info('未发现订阅的老师')


def run_sub_single_star_code(star_info):
    if star_info["movie_list"]:
        for movie in star_info["movie_list"]:
            # 判断movie['status'] == 0，以及movie['release_date']是否大于monitor_date,如果是则提交下载
            if movie["status"] == 0:
                if movie["release_date"] >= star_info["monitor_date"]:
                    _LOGGER.info(f'开始搜索「{star_info["star_name"]}」的影片「{movie["movie_code"]}」')
                    code_sub_result = torrent_main(movie["movie_code"])
                    if code_sub_result["flag"] == 0:
                        _LOGGER.error(
                            f'「{movie["movie_code"]}」下载失败，错误信息：{code_sub_result["sub_result"]}')
                        add_un_download_list(movie['movie_code'])
                        time.sleep(30)
                        continue
                    elif code_sub_result["flag"] == 1:
                        _LOGGER.info(f'「{movie["movie_code"]}」下载成功')
                        movie["status"] = 1
                        time.sleep(30)
                        continue
                    else:
                        _LOGGER.error(
                            f'「{movie["movie_code"]}」下载失败，错误信息：{code_sub_result["sub_result"]}')
                        movie["status"] = 1
                        time.sleep(30)
                        continue
        _LOGGER.info(f'{star_info["star_name"]}的影片搜索完成')
        set_cache(sign=star_info["star_name"], value=star_info)
    else:
        _LOGGER.info(f'「{star_info["star_name"]}」无影片记录')


def torrent_main(code):
    code_sub_result = {
        "code": code,
        "sub_result": "",
        "flag": 0,
        "caption": "",
        "torrent": "",
    }
    torrents = mteam_crawl().search_mteam(keyword=code)
    if torrents:
        best_torrent = get_best_torrent(torrents)
        if best_torrent:
            _LOGGER.info(f'找到最佳种子：标题：{best_torrent["title"]}，下载地址：{best_torrent["download_url"]}')
            torrent_path = download_torrent(code, best_torrent['download_url'], torrent_folder)
            if torrent_path:
                _LOGGER.info(f'「{code}」种子下载成功')
            else:
                _LOGGER.error(f'「{code}」种子下载失败，下载地址：{best_torrent["download_url"]}')
                code_sub_result["flag"] = 0
                code_sub_result[
                    "sub_result"] = f'「{code}」种子下载失败，请检查站点连通性，下载地址：{best_torrent["download_url"]}'
                return code_sub_result
            caption, pic = best_torrent_echo(best_torrent)
            res = download(torrent_path=torrent_path, save_path=event_var.down_path, category=None,
                           client_name=event_var.client_name)
            if res:
                _LOGGER.info(f'「{code}」提交下载成功')
                code_sub_result["sub_result"] = f'「{code}」提交下载成功'
                code_sub_result["flag"] = 1
                code_sub_result["caption"] = caption
                code_sub_result["torrent"] = best_torrent
                add_download_list(code)
                send_notify(f'{code_sub_result["sub_result"]}\n', code_sub_result["caption"], pic)
                return code_sub_result
            else:
                _LOGGER.info(f'「{code}」提交下载失败，可能是下载器已存在该种子')
                code_sub_result["sub_result"] = f'「{code}」提交下载失败，可能是下载器已存在该种子'
                code_sub_result["flag"] = 2
                code_sub_result["caption"] = caption
                code_sub_result["torrent"] = best_torrent
                send_notify(f'{code_sub_result["sub_result"]}\n', code_sub_result["caption"], pic)
                return code_sub_result
        else:
            _LOGGER.error(f'「{code}」没有找到合适的种子')
            code_sub_result["flag"] = 0
            code_sub_result["sub_result"] = f'「{code}」没有找到合适的种子'
            return code_sub_result
    else:
        _LOGGER.error(f'「{code}」没有找到任何资源')
        code_sub_result["flag"] = 0
        code_sub_result["sub_result"] = f'「{code}」没有找到任何资源'
        return code_sub_result
