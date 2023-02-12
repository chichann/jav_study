from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging

from .jav_study import torrent_main, run_and_download_list, un_download_research
from .common import set_true_code, add_un_download_list, judge_never_sub

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
        if not judge_never_sub(code):
            return PluginCommandResponse(True, f'番号「{code}」已经订阅过了')
        sub_result, flag = torrent_main(code)
        if flag == 1:
            return PluginCommandResponse(True, f'番号「{code}」提交订阅成功')
        elif flag == 0:
            add_un_download_list(code)
            return PluginCommandResponse(True, f'番号「{code}」已提交订阅但未找到资源，已添加至未下载列表')
        else:
            return PluginCommandResponse(False, f'番号「{code}」提交订阅失败，错误信息：{sub_result}')
    except Exception as e:
        logging.error(f'番号提交搜索失败，错误信息：{e}', exc_info=True)
        return PluginCommandResponse(False, f'番号提交搜索失败，错误信息：{e}')


@plugin.command(name='jav_research_command', title='JAV订阅未下载重新搜索', desc='点击执行JAV订阅未下载重新搜索', icon='AutoAwesome',
                run_in_background=True)
def jav_research_command(ctx: PluginCommandContext):
    try:
        un_download_research()
    except Exception as e:
        logging.error(f'JAV订阅未下载重新搜索失败，错误信息：{e}', exc_info=True)
