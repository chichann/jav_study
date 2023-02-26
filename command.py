from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.core.params import ArgSchema, ArgType
from mbot.openapi import mbot_api

import logging

from .jav_study import torrent_main, run_and_download_list, un_download_research, get_sub_code_list, delete_code_sub, \
    sub_by_star, run_sub_star_record, get_sub_star_list, delete_star_sub, sync_emby_lib
from .common import set_true_code, add_un_download_list, judge_never_sub
from .event import event_var
from .embyapi import EmbyApi

emby = EmbyApi()
server = mbot_api

_LOGGER = logging.getLogger(__name__)


@plugin.command(name='jav_sub_code', title='订阅番号', desc='输入番号自动搜索提交下载', icon='AutoAwesome',
                run_in_background=True)
def jav_sub_code_command(
        ctx: PluginCommandContext,
        code: ArgSchema(ArgType.String, '番号', '输入番号自动提交搜索下载')
):
    try:
        code = set_true_code(code)
        _LOGGER.info(f'番号「{code}」提交搜索')
        if judge_never_sub(code):
            _LOGGER.info(f'番号「{code}」已经订阅过了')
            return PluginCommandResponse(True, f'番号「{code}」已经订阅过了')
        code_sub_result = torrent_main(code, task='remote')
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
        date: ArgSchema(ArgType.String, '日期', '输入日期，监控该日期以后发行的片，格式为：2021-01-01')
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


task_list = [
    {
        "name": "榜单TOP20同步",
        "value": "jav_list"
    },
    {
        "name": "番号订阅",
        "value": "sub_code"
    },
    {
        "name": "老师订阅",
        "value": "sub_star"
    },
    {
        "name": "订阅记录同步emby库存",
        "value": "sub_sync"
    }
]


@plugin.command(name='jav_sub_research_command', title='学习资料手动执行任务', desc='点击手动选择执行学习资料任务',
                icon='AutoAwesome', run_in_background=True)
def jav_sub_research_command(ctx: PluginCommandContext,
                             task: ArgSchema(ArgType.Enum, '任务', '选择任务', enum_values=lambda: task_list,
                                             multi_value=False)):
    try:
        if task == "sub_code":
            _LOGGER.info(f'番号订阅重新搜索')
            un_download_research()
            return PluginCommandResponse(True, f'订阅中重新搜索完成')
        elif task == "sub_star":
            _LOGGER.info(f'老师订阅重新搜索')
            run_sub_star_record(task='local')
            return PluginCommandResponse(True, f'订阅中重新搜索完成')
        elif task == "jav_list":
            if event_var.jav_list_enable:
                _LOGGER.info(f'榜单TOP20开始同步')
                run_and_download_list()
                return PluginCommandResponse(True, f'榜单TOP20同步完成')
            else:
                _LOGGER.error(f'未开启自动下载榜单TOP20,请先在配置中打开开关。')
                return PluginCommandResponse(False, f'最受欢迎影片重新搜索失败，错误信息：未开启最受欢迎影片')
        elif task == "sub_sync":
            if emby.is_emby:
                _LOGGER.info(f'订阅记录同步emby库存')
                sync_emby_lib()
                _LOGGER.info(f'订阅记录同步emby库存完成')
                return PluginCommandResponse(True, f'订阅记录同步emby库存完成')
            else:
                _LOGGER.error(f'订阅记录同步emby库存失败，错误信息：未配置emby')
                return PluginCommandResponse(False, f'订阅记录同步emby库存失败，错误信息：未配置emby')
    except Exception as e:
        logging.error(f'订阅未下载重新搜索失败，错误信息：{e}', exc_info=True)


@plugin.command(name='jav_sub_code_delete', title='删除番号订阅', desc='选择番号删除订阅', icon='AutoAwesome',
                run_in_background=True)
def jav_sub_code_delete(ctx: PluginCommandContext,
                        code: ArgSchema(ArgType.Enum, '番号', '选择番号删除订阅',
                                        enum_values=get_sub_code_list)
                        ):
    try:
        if delete_code_sub(code):
            return PluginCommandResponse(True, f'番号「{code}」删除成功')
        else:
            return PluginCommandResponse(False, f'番号「{code}」删除失败')
    except Exception as e:
        logging.error(f'番号订阅删除失败，错误信息：{e}', exc_info=True)
        return PluginCommandResponse(False, f'番号订阅删除失败，错误信息：{e}')


@plugin.command(name='jav_sub_star_delete', title='删除老师订阅', desc='选择老师删除订阅', icon='AutoAwesome',
                run_in_background=True)
def jav_sub_star_delete(ctx: PluginCommandContext,
                        star: ArgSchema(ArgType.Enum, '老师', '选择老师删除订阅。',
                                        enum_values=get_sub_star_list)
                        ):
    try:
        if delete_star_sub(star):
            return PluginCommandResponse(True, f'老师「{star}」删除成功')
        else:
            return PluginCommandResponse(False, f'老师「{star}」删除失败')
    except Exception as e:
        logging.error(f'老师订阅删除失败，错误信息：{e}', exc_info=True)
        return PluginCommandResponse(False, f'老师订阅删除失败，错误信息：{e}')

#
# @plugin.command(name='restart_app', title='重启程序', desc='点击重启程序', icon='AutoAwesome',
#                 run_in_background=True)
# def jav_sub_star_delete(ctx: PluginCommandContext):
#     try:
#         _LOGGER.info(f'重启程序')
#         server.common.restart_app()
#     except Exception as e:
#         logging.error(f'重启程序失败，错误信息：{e}', exc_info=True)
#         return PluginCommandResponse(False, f'重启程序失败，错误信息：{e}')
#