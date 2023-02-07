import _md5
from .jav_study import *
import logging
import random
import requests

_LOGGER = logging.getLogger(__name__)


# 把str计算md5
def md5(str_before):
    m = _md5.md5()
    m.update(str_before.encode('utf-8'))
    return m.hexdigest()


# 生成10位数字随机数
def random_num():
    return str(random.randint(1000000000, 9999999999))


def req_trans(query, appid, sercet):
    try:
        q = query.encode('utf-8').decode('utf-8')
        salt = random_num()
        # 拼接字符串
        str_after = appid + q + salt + sercet
        # 计算md5
        sign = md5(str_after)
        url = f'http://api.fanyi.baidu.com/api/trans/vip/translate?q={q}&from=auto&to=zh&appid={appid}&salt={salt}&sign={sign}'
        res = requests.get(url).json()
        dst = res['trans_result'][0]['dst']
        return dst
    except Exception as e:
        _LOGGER.error(f'翻译失败，错误详情：{e}')
        return None


def trans_main(from_str, appid, sercet):
    return req_trans(from_str, appid, sercet)
