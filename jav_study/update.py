import logging
import requests
import os
import zipfile
import base64

from mbot.openapi import mbot_api

from .event import event_var

server = mbot_api
_LOGGER = logging.getLogger(__name__)


def update_self():
    update_dir = '/data/plugins/jav_study/update/'
    if not os.path.exists(update_dir):
        _LOGGER.info(f'创建update文件夹')
        os.mkdir(update_dir)
    base_url = 'aHR0cHM6Ly9naXRodWIuY29tL2NoaWNoYW5uL2phdl9zdHVkeS9yZWxlYXNlcy9sYXRlc3Q='
    try:
        r = requests.get(base64.b64decode(base_url).decode("utf-8"),
                         proxies=event_var.proxies, timeout=30)
    except Exception as e:
        _LOGGER.error(f'查询最新版本号出错，原因为：{e}')
        return False
    res_url = r.url
    remote_v = res_url.split('/v')[-1]
    with open('/data/plugins/jav_study/manifest.json', 'r') as f:
        version = f.read().split('"version": "')[1].split('",')[0]
    if version == remote_v:
        _LOGGER.info(f'版本一致,不需要更新')
        return True
    else:
        _LOGGER.info(f'本地版本为v{version},远程版本为v{remote_v},需要更新')
        base_url = 'aHR0cHM6Ly9naXRodWIuY29tL2NoaWNoYW5uL2phdl9zdHVkeS9hcmNoaXZlL3JlZnMvdGFncy92'
        try:
            r = requests.get(f'{base64.b64decode(base_url).decode("utf-8")}{remote_v}.zip',
                             proxies=event_var.proxies, timeout=30)
        except Exception as e:
            _LOGGER.error(f'下载最新版本出错，原因为：{e}')
            return False
        with open(f'{update_dir}v{remote_v}.zip', 'wb') as f:
            f.write(r.content)
            _LOGGER.info(f'下载最新v{remote_v}版本成功')
        with zipfile.ZipFile(f'{update_dir}v{remote_v}.zip', 'r') as zip_ref:
            zip_ref.extractall(f'{update_dir}v{remote_v}')
            _LOGGER.info(f'解压v{remote_v}版本成功')
        os.system(f'cp -rf {update_dir}v{remote_v}/jav_study-{remote_v}/jav_study/* /data/plugins/jav_study/')
        os.system(f'rm -rf {update_dir}v{remote_v}/')
        os.system(f'rm -rf {update_dir}v{remote_v}.zip')
        _LOGGER.info(f'更新v{remote_v}版本成功')
        _LOGGER.info(f'重启主程序')
        server.common.restart_app()
    return True

def install_update_mdc():
    update_dir = '/data/plugins/jav_study/update/'
    if not os.path.exists(update_dir):
        _LOGGER.info(f'创建update文件夹')
        os.mkdir(update_dir)
    mdc_dir = '/data/plugins/mdc_mbot_plugin/'
    if not os.path.exists(mdc_dir):
        _LOGGER.info('MDC-NG插件未安装，现在开始安装。')
        os.mkdir(mdc_dir)
        flag = 0
    else:
        flag = 1
    base_url = 'aHR0cHM6Ly9naXRodWIuY29tL21kYy1uZy9tZGNfbWJvdF9wbHVnaW4vcmVsZWFzZXMvbGF0ZXN0'
    try:
        r = requests.get(base64.b64decode(base_url).decode("utf-8"),
                         proxies=event_var.proxies, timeout=30)
    except Exception as e:
        _LOGGER.error(f'查询MDC-NG版本出错，原因为：{e}')
        return False
    res_url = r.url
    remote_v = res_url.split('/v')[-1]
    if flag == 1:
        with open(f'{mdc_dir}manifest.json', 'r') as f:
            version = f.read().split('"version": "')[1].split('",')[0]
        if version == remote_v:
            _LOGGER.info(f'MDC-NG版本一致,不需要更新')
            return True
        else:
            _LOGGER.info(f'MDC-NG本地版本为v{version},远程版本为v{remote_v},需要更新')
    base_url = 'aHR0cHM6Ly9naXRodWIuY29tL21kYy1uZy9tZGNfbWJvdF9wbHVnaW4vYXJjaGl2ZS9yZWZzL3RhZ3Mvdg=='
    try:
        r = requests.get(f'{base64.b64decode(base_url).decode("utf-8")}{remote_v}.zip',
                         proxies=event_var.proxies, timeout=30)
    except Exception as e:
        _LOGGER.error(f'下载MDC-NG最新版本出错，原因为：{e}')
        return False
    with open(f'{update_dir}v{remote_v}.zip', 'wb') as f:
        f.write(r.content)
        _LOGGER.info(f'下载MDC-NG最新v{remote_v}版本成功')
    with zipfile.ZipFile(f'{update_dir}v{remote_v}.zip', 'r') as zip_ref:
        zip_ref.extractall(f'{update_dir}v{remote_v}')
        _LOGGER.info(f'解压MDC-NG v{remote_v}版本成功')
    os.system(f'cp -rf {update_dir}v{remote_v}/mdc_mbot_plugin-{remote_v}/* /data/plugins/mdc_mbot_plugin/')
    os.system(f'rm -rf {update_dir}v{remote_v}/')
    os.system(f'rm -rf {update_dir}v{remote_v}.zip')
    _LOGGER.info(f'安装MDC-NG v{remote_v}版本成功')
    _LOGGER.info(f'重启主程序')
    server.common.restart_app()
    return True
