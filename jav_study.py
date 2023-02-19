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
from .crawl import jav_crawl, mteam_crawl

server = mbot_api
_LOGGER = logging.getLogger(__name__)
torrent_folder = '/data/plugins/jav_study/torrents'
if not os.path.exists(torrent_folder):
    os.makedirs(torrent_folder)


@plugin.task('jav_list_task', '定时爬取JAV影片榜单', cron_expression='34 */6 * * *')
def jav_list_task():
    run_and_download_list()


@plugin.task('un_download_code_research_task', 'JAV订阅中重新搜索资源', cron_expression='16 7,17 * * *')
def un_download_code_research_task():
    un_download_research()


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
        set_cache(sign='un_download_code', code_list=un_download_code)


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


def get_jav_sub_list():
    un_download_code = get_cache(sign='un_download_code')
    if un_download_code:
        # 把列表un_download_code中的每个值转成字典格式,参数有name和value
        sub_list = [{'name': code, 'value': code} for code in un_download_code]
        return sub_list


def delete_jav_sub(code):
    _LOGGER.info(f'开始删除订阅「{code}」')
    code = ''.join(code)
    un_download_code = get_cache(sign='un_download_code')
    if un_download_code:
        if code in un_download_code:
            un_download_code.remove(code)
            _LOGGER.info(f'删除订阅「{code}」成功')
            set_cache(sign='un_download_code', code_list=un_download_code)
            return True
        else:
            return False


def run_and_download_list():
    result = jav_crawl().get_jav_like()
    try:
        if result:
            code_list = like_list_judge(result)
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
                code_sub_result["sub_result"] = f'「{code}」种子下载失败，请检查站点连通性，下载地址：{best_torrent["download_url"]}'
                return code_sub_result
            caption, pic = best_torrent_echo(best_torrent)
            res = download(torrent_path=torrent_path, save_path=event_var.down_path, category=None,
                           client_name=event_var.client_name)
            if res:
                _LOGGER.info(f'「{code}」提交下载成功')
                code_sub_result["sub_result"] = f'「{code}」提交下载成功\n'
                code_sub_result["flag"] = 1
                code_sub_result["caption"] = caption
                code_sub_result["torrent"] = best_torrent
                add_download_list(code)
                return code_sub_result
            else:
                _LOGGER.info(f'「{code}」提交下载失败，可能是下载器已存在该种子')
                code_sub_result["sub_result"] = f'「{code}」提交下载失败，可能是下载器已存在该种子\n'
                code_sub_result["flag"] = 2
                code_sub_result["caption"] = caption
                code_sub_result["torrent"] = best_torrent
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
