from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
import logging

_LOGGER = logging.getLogger(__name__)
server = mbot_api


def jav_list_echo(result):
    caption_list, img_list = [], []
    if result:
        result = judge_translate(result)
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


def judge_translate(data):
    from .event import event_var
    from .translate import trans_main
    if event_var.translate_enable:
        for item in data:
            before = item['av_title']
            after = trans_main(before)
            if after:
                item['av_title'] = after
    return data


def get_cache(sign):
    cache_list = server.common.get_cache('jav_search', sign)
    return cache_list


def set_cache(sign, value):
    try:
        server.common.set_cache('jav_search', sign, value)
        return True
    except Exception as e:
        logging.error(f'jav_study写入缓存失败，错误信息：{e}')
        return False


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


def set_true_code(code):
    code_list = code.split('-')
    code = ''.join(code_list).replace('\r', '').replace('\n', '').replace(' ', '')
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


def add_un_download_list(code):
    from .crawl import jav_crawl
    un_download_code = get_cache(sign='un_download_code')
    if un_download_code:
        if code in un_download_code:
            _LOGGER.info(f'「{code}」已存在于未下载列表')
            return False
        un_download_code.append(code)
    else:
        un_download_code = [code]
    if set_cache(sign='un_download_code', value=un_download_code):
        _LOGGER.info(f'「{code}」已添加到未下载列表，等待下次重试。')
        caption, pic = jav_list_echo(jav_crawl().jav_search(code))
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
    if set_cache(sign='downloaded_code', value=downloaded_code):
        _LOGGER.info(f'「{code}」已添加到已下载列表，不会再重复下载。')
        return True


def judge_never_sub(code):
    exist_list = []
    un_download_code = get_cache(sign='un_download_code')
    downloaded_code = get_cache(sign='downloaded_code')
    if un_download_code:
        exist_list.extend(un_download_code)
    if downloaded_code:
        exist_list.extend(downloaded_code)
    if code in exist_list:
        _LOGGER.error(f'「{code}」已经订阅过了。')
        return False
    return True


def send_notify(title, content, pic):
    from .event import event_var
    channel_item = event_var.channel
    if event_var.message_to_uid:
        for _ in event_var.message_to_uid:
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
