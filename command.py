from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging

from .jav_study import torrent_main, run_and_download_list, un_download_research, get_jav_sub_list, delete_jav_sub, sub_by_star
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


@plugin.command(name='jav_sub_code', title='订阅番号', desc='输入番号自动搜索提交下载', icon='AutoAwesome',
                run_in_background=True)
def jav_sub_code_command(
        ctx: PluginCommandContext,
        code: ArgSchema(ArgType.String, '番号', '输入番号自动提交搜索下载')
):
    try:
        code = set_true_code(code)
        _LOGGER.info(f'番号「{code}」提交搜索')
        if not judge_never_sub(code):
            return PluginCommandResponse(True, f'番号「{code}」已经订阅过了')
        code_sub_result= torrent_main(code)
        if code_sub_result["flag"] == 1:
            return PluginCommandResponse(True, f'番号「{code}」提交订阅成功')
        elif code_sub_result["flag"] == 0:
            add_un_download_list(code)
            return PluginCommandResponse(True, f'番号「{code}」已提交订阅但未找到资源，已添加至未下载列表')
        else:
            return PluginCommandResponse(False, f'番号「{code}」提交订阅失败，错误信息：{code_sub_result["sub_result"]}')
    except Exception as e:
        logging.error(f'番号提交搜索失败，错误信息：{e}', exc_info=True)
        return PluginCommandResponse(False, f'番号提交搜索失败，错误信息：{e}')


@plugin.command(name='jav_sub_star', title='订阅老师', desc='点击订阅老师相关资料', icon='AutoAwesome',
                run_in_background=True)
def jav_sub_star_command(
        ctx: PluginCommandContext,
        star: ArgSchema(ArgType.String, '老师名字', '输入老师名字'),
        date: ArgSchema(ArgType.String, '日期', '输入日期，格式为：2021-01-01')
):
    try:
        _LOGGER.info(f'老师「{star}」提交订阅')
        if sub_by_star(star, date):
            return PluginCommandResponse(True, f'老师「{star}」提交订阅成功')
        else:
            return PluginCommandResponse(False, f'老师「{star}」提交订阅失败')
    except Exception as e:
        logging.error(f'老师提交订阅失败，错误信息：{e}', exc_info=True)
        return PluginCommandResponse(False, f'老师提交订阅失败，错误信息：{e}')


@plugin.command(name='jav_research_command', title='JAV订阅中重新搜索', desc='点击执行JAV订阅中番号重新搜索',
                icon='AutoAwesome', run_in_background=True)
def jav_research_command(ctx: PluginCommandContext):
    try:
        un_download_research()
    except Exception as e:
        logging.error(f'JAV订阅未下载重新搜索失败，错误信息：{e}', exc_info=True)


@plugin.command(name='jav_sub_delete', title='JAV订阅删除', desc='选择番号删除订阅', icon='AutoAwesome',
                run_in_background=True)
def jav_sub_delete(ctx: PluginCommandContext,
                   code: ArgSchema(ArgType.Enum, '番号', '选择番号删除订阅，仅支持单次删除一个。',
                                   enum_values=get_jav_sub_list)
                   ):
    try:
        if delete_jav_sub(code):
            return PluginCommandResponse(True, f'番号「{code}」删除成功')
        else:
            return PluginCommandResponse(False, f'番号「{code}」删除失败')
    except Exception as e:
        logging.error(f'JAV订阅删除失败，错误信息：{e}', exc_info=True)
        return PluginCommandResponse(False, f'JAV订阅删除失败，错误信息：{e}')
