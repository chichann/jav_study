from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api

import requests
import logging
import os.path
import time
import random

from .event import event_var
from .download_client import download
from .torrent import get_best_torrent, best_torrent_echo, download_torrent
from .common import get_cache, set_cache, add_un_download_list, add_download_list, send_notify, judge_never_sub
from .crawl import jav_crawl, site_torrent_crawl, javbus_crawl
from .embyapi import EmbyApi

server = mbot_api
emby = EmbyApi()
_LOGGER = logging.getLogger(__name__)
torrent_folder = '/data/plugins/jav_study/torrents'
if not os.path.exists(torrent_folder):
    os.makedirs(torrent_folder)


@plugin.task('jav_list_task', '定时爬取榜单TOP20', cron_expression='34 */6 * * *')
def jav_list_task():
    if event_var.jav_list_enable:
        run_and_download_list()


@plugin.task('un_download_code_research_task', '番号订阅重新搜索', cron_expression='16 7,17 * * *')
def un_download_code_research_task():
    un_download_research()


@plugin.task('research_star_sub', '老师订阅重新搜索', cron_expression='15 8,18 * * *')
def research_star_sub_task():
    search_code_by_star_record()
    run_sub_star_record()


@plugin.task('sync_emby_lib', '同步emby库存信息', cron_expression='0 */6 * * *')
def sync_emby_lib_task():
    if emby.is_emby:
        sync_emby_lib()


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
        _LOGGER.info(f'休息10-20秒继续下一个')
        time.sleep(random.randint(10, 20))
    if downloaded_code_now:
        for item in downloaded_code_now:
            un_download_code.remove(item)
        set_cache(sign='un_download_code', value=un_download_code)


def sync_emby_lib():
    un_download_code = get_cache(sign='un_download_code') or []
    in_lib_list = [item for item in un_download_code if emby.check_emby_item(item)]
    if in_lib_list:
        for item in in_lib_list:
            _LOGGER.info(f'「{item}」已经在emby库中，删除未下载列表中的记录')
            un_download_code.remove(item)
        set_cache(sign='un_download_code', value=un_download_code)


def search_list_judge_recorded(code_list_before):
    code_list = [item['av_id'] for item in code_list_before]
    exist_list = (get_cache(sign='downloaded_code') or []) + (get_cache(sign='un_download_code') or [])
    code_list_after = [item for item in code_list if item not in exist_list and not emby.check_emby_item(item)]
    return code_list_after


def get_sub_code_list():
    un_download_code = get_cache(sign='un_download_code')
    if un_download_code:
        # 把列表un_download_code中的每个值转成字典格式,参数有name和value
        sub_list = [{'name': code, 'value': code} for code in un_download_code]
        return sub_list


def delete_code_sub(code):
    _LOGGER.info(f'开始删除订阅「{code}」')
    for code_item in code:
        un_download_code = get_cache(sign='un_download_code')
        if un_download_code:
            if code_item in un_download_code:
                un_download_code.remove(code_item)
                _LOGGER.info(f'删除订阅「{code_item}」成功')
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
    for star_item in star_name:
        sub_star = get_cache(sign='actor_sub')
        if sub_star:
            for item in sub_star:
                if item['star_name'] == star_item:
                    if event_var.smms_token:
                        del_url = item['del_avatar_img']
                        del_avatar_img(del_url)
                    sub_star.remove(item)
                    _LOGGER.info(f'删除订阅「{star_item}」成功')
                    set_cache(sign='actor_sub', value=sub_star)
                    set_cache(sign=star_item, value=[])
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
                _LOGGER.info(f'榜单TOP20本次新增{"、".join(code_list)},共{len(code_list)}部')
            if code_list:
                for code in code_list:
                    _LOGGER.info(f'番号「{code}」提交搜索')
                    code_sub_result = torrent_main(code)
                    if code_sub_result["flag"] == 0:
                        _LOGGER.error(f'榜单TOP20{code_sub_result["sub_result"]}')
                        add_un_download_list(code)
                        _LOGGER.info(f'休息10-20秒继续下一个')
                        time.sleep(random.randint(10, 20))
                        continue
                    elif code_sub_result["flag"] == 1:
                        _LOGGER.info(f'榜单TOP20{code_sub_result["sub_result"]}')
                        _LOGGER.info(f'休息10-20秒继续下一个')
                        time.sleep(random.randint(10, 20))
                        continue
                    else:
                        _LOGGER.error(f'榜单TOP20{code_sub_result["sub_result"]}')
                        _LOGGER.info(f'休息10-20秒继续下一个')
                        time.sleep(random.randint(10, 20))
                        continue
                _LOGGER.info('榜单TOP20本次新增影片搜索完成')
            else:
                _LOGGER.error('榜单TOP20无更新新片')
                return True
        else:
            return False
    except Exception as e:
        logging.error(f'榜单TOP20获取失败，错误信息：{e}', exc_info=True)
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
        for sub_item in actor_sub:
            if sub_item["star_name"] == star:
                sub_item["monitor_date"] = date
                star_info = get_cache(sign=sub_item["star_name"])
                star_info["monitor_date"] = date
                set_cache(sign='actor_sub', value=actor_sub)
                set_cache(sign=sub_item["star_name"], value=star_info)
                return {'flag': True, 'star_info': sub_item}
    return {'flag': False}


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
                if movie["movie_code"] not in [x["movie_code"] for x in star_info["movie_list"]]:
                    star_info["movie_list"].append(movie)
    for movie in star_info["movie_list"]:
        if movie["status"] == 0:
            judge = judge_never_sub(movie["movie_code"])
            if judge:
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
                if judge_never_sub(movie["movie_code"]):
                    movie["status"] = 1
                    continue
                if movie["release_date"] >= star_info["monitor_date"]:
                    _LOGGER.info(f'开始搜索「{star_info["star_name"]}」的影片「{movie["movie_code"]}」')
                    code_sub_result = torrent_main(movie["movie_code"])
                    if code_sub_result["flag"] == 0:
                        _LOGGER.error(
                            f'「{movie["movie_code"]}」下载失败，错误信息：{code_sub_result["sub_result"]}')
                        add_un_download_list(movie['movie_code'])
                        _LOGGER.info(f'休息10-20秒继续下一个')
                        time.sleep(random.randint(10, 20))
                        continue
                    elif code_sub_result["flag"] == 1:
                        _LOGGER.info(f'「{movie["movie_code"]}」下载成功')
                        movie["status"] = 1
                        _LOGGER.info(f'休息10-20秒继续下一个')
                        time.sleep(random.randint(10, 20))
                        continue
                    else:
                        _LOGGER.error(
                            f'「{movie["movie_code"]}」下载失败，错误信息：{code_sub_result["sub_result"]}')
                        movie["status"] = 1
                        _LOGGER.info(f'休息10-20秒继续下一个')
                        time.sleep(random.randint(10, 20))
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
    torrents = site_torrent_crawl().search_by_keyword(keyword=code)
    if torrents:
        best_torrent = get_best_torrent(torrents)
        if best_torrent:
            _LOGGER.info(f'找到最佳种子：标题：{best_torrent["name"]}，下载地址：{best_torrent["download_url"]}')
            torrent_path = download_torrent(code, best_torrent, torrent_folder)
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
                code_sub_result["pic"] = pic
                add_download_list(code)
                send_notify(f'{code_sub_result["sub_result"]}\n', code_sub_result["caption"], code_sub_result["pic"])
                return code_sub_result
            else:
                _LOGGER.info(f'「{code}」提交下载失败，可能是下载器已存在该种子')
                code_sub_result["sub_result"] = f'「{code}」提交下载失败，可能是下载器已存在该种子'
                code_sub_result["flag"] = 2
                code_sub_result["caption"] = caption
                code_sub_result["torrent"] = best_torrent
                code_sub_result["pic"] = pic
                send_notify(f'{code_sub_result["sub_result"]}\n', code_sub_result["caption"], code_sub_result["pic"])
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
