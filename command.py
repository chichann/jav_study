from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging

from .jav_study import *

_LOGGER = logging.getLogger(__name__)


@plugin.command(name='jav_list', title='JAV最受欢迎影片', desc='点击获取JAV最受欢迎影片', icon='AutoAwesome',
                run_in_background=True)
def jav_list_command(ctx: PluginCommandContext):
    try:
        run_and_download_list()
        return PluginCommandResponse(True, f'JAV最受欢迎影片获取成功')
    except Exception as e:
        logging.error(f'JAV最受欢迎影片获取失败，错误信息：{e}', exc_info=True)
        return PluginCommandResponse(False, f'JAV最受欢迎影片获取失败，错误信息：{e}')


@plugin.command(name='jav_search', title='番号搜索', desc='输入番号自动搜索提交下载', icon='AutoAwesome',
                run_in_background=True)
def jav_search_command(
        ctx: PluginCommandContext,
        code: ArgSchema(ArgType.String, '番号', '输入番号自动提交搜索下载')
):
    try:
        code = set_true_code(code)
        _LOGGER.info(f'番号「{code}」提交搜索')
        sub_result, flag = torrent_main(code)
        if flag == 1:
            return PluginCommandResponse(True, f'番号「{code}」提交搜索')
        else:
            add_un_download_list(code)
            return PluginCommandResponse(True, f'未找到资源，已添加至未下载列表')
    except Exception as e:
        logging.error(f'番号提交搜索失败，错误信息：{e}', exc_info=True)
        return PluginCommandResponse(False, f'番号提交搜索失败，错误信息：{e}')

