from mbot.openapi import mbot_api
from .event import event_var
import logging
import requests
import os
import zipfile
server = mbot_api
_LOGGER = logging.getLogger(__name__)


def update():
    update_dir = '/data/plugins/jav_study/update/'
    if not os.path.exists(update_dir):
        _LOGGER.info(f'创建update文件夹')
        os.mkdir(update_dir)
    url = 'https://github.com/chichann/jav_study/releases/latest'
    try:
        r = requests.get(url, proxies=event_var.proxies, timeout=30)
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
        try:
            url = f'https://github.com/chichann/jav_study/archive/refs/tags/v{remote_v}.zip'
        except Exception as e:
            _LOGGER.error(f'下载最新版本出错，原因为：{e}')
            return False
        r = requests.get(url, proxies=event_var.proxies, timeout=30)
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
