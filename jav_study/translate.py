import _md5
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
        if 'trans_result' in res:
            dst = res['trans_result'][0]['dst']
            return dst
        elif 'error_code' in res:
            msg = {"error_code": res["error_code"], "error_msg": res["error_msg"], "错误详情查询": "http://api.fanyi.baidu.com/doc/21"}
            _LOGGER.error(f'翻译失败，错误信息：{msg}')
    except Exception as e:
        logging.error(f'翻译失败，错误信息：{e}', exc_info=True)
        return None


def trans_main(from_str):
    from .event import event_var
    appid = event_var.appid
    sercet = event_var.sercet
    return req_trans(from_str, appid, sercet)
