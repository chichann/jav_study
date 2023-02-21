from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from mbot.common.flaskutils import api_result

from flask import Blueprint, request
import logging

from .crawl import jav_crawl
from .common import send_notify, add_un_download_list, jav_list_echo, judge_never_sub, set_true_code
from .jav_study import torrent_main

server = mbot_api
_LOGGER = logging.getLogger(__name__)

bp = Blueprint('jav_study', __name__)
"""
把flask blueprint注册到容器
这个URL访问完整的前缀是 /api/plugins/你设置的前缀
"""
plugin.register_blueprint('jav_study', bp)


@bp.route('/search', methods=["GET"])
def search():
    from .common import judge_translate
    keyword = request.args.get('keyword') if request.args.get('keyword') else ''
    if keyword:
        search_result_json: list = jav_crawl().jav_search(keyword)
        if search_result_json is not None:
            search_result_json = judge_translate(search_result_json)
            return api_result(code=0, message='查询成功', data=search_result_json)
        else:
            return api_result(code=1, message='查询失败,请查看日志', data='')
    else:
        return api_result(code=1, message='请输入关键字', data='')


@bp.route('/list', methods=["GET"])
def like_list():
    result: list = jav_crawl().get_jav_like()
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
        code = set_true_code(code)
        _LOGGER.info(f'番号「{code}」提交搜索')
        if not judge_never_sub(code):
            return api_result(code=1, message='订阅失败', data=f'「{code}」已经订阅过了')
        else:
            code_sub_result = torrent_main(code)
            if code_sub_result["flag"] == 1:
                return api_result(code=0, message='订阅并下载成功', data=code_sub_result["sub_result"])
            elif code_sub_result["flag"] == 0:
                add_un_download_list(code)
                return api_result(code=0, message='订阅成功，但找不到资源', data=code_sub_result["sub_result"])
            else:
                return api_result(code=1, message='订阅失败', data=code_sub_result["sub_result"])
    else:
        return api_result(code=1, message='请输入番号', data='')


@bp.route('/tg_sub', methods=["GET"])
def tg_sub():
    code = request.args.get('code') if request.args.get('code') else ''
    if code:
        code = set_true_code(code)
        _LOGGER.info(f'番号「{code}」提交搜索')
        if not judge_never_sub(code):
            return api_result(code=1, message='订阅失败', data=f'「{code}」已经订阅过了')
        else:
            code_sub_result = torrent_main(code)
            if code_sub_result["flag"] == 1:
                return api_result(code=0, message='订阅并下载成功', data=code_sub_result)
            elif code_sub_result["flag"] == 0:
                add_un_download_list(code)
                return api_result(code=0, message='订阅成功，但找不到资源', data=code_sub_result)
            else:
                return api_result(code=1, message='订阅失败', data=code_sub_result)
    else:
        return api_result(code=1, message='请输入番号', data='')
