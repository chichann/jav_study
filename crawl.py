from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api

import requests
from bs4 import BeautifulSoup, SoupStrainer
import logging

from .event import event_var
from .common import str_cookies_to_dict
from .translate import trans_main
from .torrent import get_weight, get_mteam_conf

_LOGGER = logging.getLogger(__name__)


class jav_crawl:

    def __init__(self):
        self.headers = event_var.headers
        self.proxies = event_var.proxies
        self.appid = event_var.appid
        self.sercet = event_var.sercet
        self.translate_enable = event_var.translate_enable

    def get_jav_like(self):
        url = 'https://www.javlibrary.com/cn/vl_mostwanted.php?page=1'
        # result_list = []
        try:
            _LOGGER.info(f'开始获取JAV最受欢迎影片')
            r = requests.get(url=url, headers=self.headers, proxies=self.proxies, timeout=30)
            list_select = 'div.videos > div.video'
            soup_tmp = SoupStrainer('div', {'class': 'videos'})
            soup = BeautifulSoup(r.text, 'html.parser', parse_only=soup_tmp)
            av_list = soup.select(list_select)
            result_list = self.jav_list_result(av_list)
            if result_list:
                return result_list
            else:
                return False
        except Exception as e:
            logging.error(f'获取JAV最受欢迎影片失败，原因为{e}', exc_info=True)
            return False

    def jav_search(self, keyword):
        from .common import set_true_code
        code = set_true_code(keyword)
        url = f'https://www.javlibrary.com/cn/vl_searchbyid.php?keyword={code}'
        result_list = []
        try:
            _LOGGER.info(f'开始在javlibrary查询「{code}」')
            r = requests.get(url=url, headers=self.headers, proxies=self.proxies, timeout=30)
            list_select = 'div.videos > div.video'
            soup_tmp = SoupStrainer('div', {'class': 'videos'})
            soup = BeautifulSoup(r.text, 'html.parser', parse_only=soup_tmp)
            av_list = soup.select(list_select)
            if av_list:
                result_list = self.jav_list_result(av_list)
            else:
                soup2_tmp = SoupStrainer('div', {'id': 'rightcolumn'})
                soup2 = BeautifulSoup(r.text, 'html.parser', parse_only=soup2_tmp)
                video_info = self.get_detail(soup2)
                if video_info:
                    result_list.append(video_info)
                else:
                    result_list = None
            if result_list is not None:
                _LOGGER.info(f'查询「{code}」成功，结果：{result_list}')
                return result_list
            else:
                _LOGGER.error(f'查询「{code}」失败，找不到结果')
                return None
        except Exception as e:
            logging.error(f'查询「{code}」失败，原因为{e}', exc_info=True)
            return None

    def jav_list_result(self, av_list):
        result_list = []
        try:
            for av in av_list:
                av_href = av.select('a')[0].get('href')
                av_href = 'https://www.javlibrary.com/cn' + av_href.strip('.')
                r = requests.get(url=av_href, headers=self.headers, proxies=self.proxies, timeout=30)
                soup_tmp = SoupStrainer('div', {'id': 'rightcolumn'})
                soup = BeautifulSoup(r.text, 'html.parser', parse_only=soup_tmp)
                video_info = self.get_detail(soup)
                result_list.append(video_info)
            return result_list
        except Exception as e:
            logging.error(f'javlibrary搜索列表解析失败，原因为{e}', exc_info=True)
            return False

    def get_detail(self, soup):
        video_info = {}
        try:
            if '搜寻没有结果' in soup.text:
                _LOGGER.error(f'javlibrary搜索列表解析失败，找不到任何结果')
                return None
            else:
                av_id = soup.select('div#video_title > h3 > a')[0].contents[0].split(' ', 1)[0]
                av_title = soup.select('div#video_title > h3 > a')[0].contents[0].split(' ', 1)[1]
                video_date = soup.select('div#video_date > table > tr > td.text')[0].contents[0]
                genres = soup.select('div#video_genres > table > tr > td.text > span.genre > a')
                genre = ''
                for i in genres:
                    genre += i.contents[0] + ' / '
                actor_select = 'div#video_cast > table > tr > td.text > span > span.star > a'
                actors = soup.select(actor_select)
                actor = ''
                for i in actors:
                    actor += i.contents[0] + ' / '
                av_img = soup.select('img#video_jacket_img')[0].get('src')
                video_info['av_id'] = av_id
                video_info['av_title'] = av_title
                video_info['av_actor'] = actor.rstrip(' / ')
                video_info['av_date'] = video_date
                video_info['av_genre'] = genre.rstrip(' / ')
                video_info['av_img'] = 'https:' + av_img
                return video_info
        except Exception as e:
            logging.error(f'javlibrary详情页解析失败，原因为{e}', exc_info=True)
            return None


class javbus_crawl:
    def __init__(self):
        self.headers = event_var.headers
        self.proxies = event_var.proxies
        # self.appid = event_var.appid
        # self.sercet = event_var.sercet
        # self.translate_enable = event_var.translate_enable

    def crawl_start_code(self, star):
        try:
            url = 'https://www.javbus.com/searchstar/' + star
            r = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30)
            soup = BeautifulSoup(r.text, 'html.parser')
            stars = soup.select('a.avatar-box')
            if len(stars) > 1:
                return None
            if len(stars) < 1:
                return None
            url = stars[0].get('href')
            star_id = url.split('/')[-1]
            star_name = stars[0].select('div.photo-frame > img')[0].get('title')
            star_avatar = 'https://www.javbus.com' + stars[0].select('div.photo-frame > img')[0].get('src')
            star_avatar = self.save_avatar_and_upload(star_name, star_avatar)
            star_detail = self.crawl_actor_detail(star_id)
            star_info = {
                'star_id': star_id, 'star_name': star_name, 'star_avatar': star_avatar, 'star_detail': star_detail}
            return star_info
        except Exception as e:
            logging.error(f'javbus搜索演员失败，原因为{e}', exc_info=True)
            return None

    def save_avatar_and_upload(self, star_name, star_avatar):
        import os
        try:
            avatar_img_path = '/plugins/jav_study/avatar_img'
            if not os.path.exists(avatar_img_path):
                os.makedirs(avatar_img_path)
            r = requests.get(star_avatar, headers=self.headers, proxies=self.proxies, timeout=30)
            if r.status_code == 200:
                with open(f'{avatar_img_path}/{star_name}.jpg', 'wb') as f:
                    f.write(r.content)
            r = requests.post('https://sm.ms/api/v2/upload',
                              headers={'Authorization': 'APUGQJKYLuNWjZv86O2Shg3CHDrRpBlV'},
                              files={'smfile': open(f'{avatar_img_path}/{star_name}.jpg', 'rb')},
                              proxies=self.proxies, timeout=30)
            if r.status_code == 200:
                return r.json()['data']['url']
            else:
                return None
        except Exception as e:
            logging.error(f'javbus保存头像并上传失败，原因为{e}', exc_info=True)
            return None

    def crawl_actor_detail(self, star_id):
        try:
            url = 'https://www.javbus.com/star/' + star_id
            r = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30)
            soup = BeautifulSoup(r.text, 'html.parser')
            actor_details = soup.select('div.avatar-box > div.photo-info > p')
            content = []
            if actor_details:
                for item in actor_details:
                    content.append(item.text)
            return content
        except Exception as e:
            logging.error(f'javbus获取演员详情失败，原因为{e}', exc_info=True)
            return None

    def crawl_list_by_star(self, star_id):
        try:
            url = 'https://www.javbus.com/star/' + star_id
            r = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30)
            soup = BeautifulSoup(r.text, 'html.parser')
            movies = soup.select('a.movie-box')
            movie_list = []
            for movie in movies:
                movie_code = movie.get('href').split('/')[-1]
                movie_name = movie.select('div.photo-info > span')[0].contents[0]
                movie_date = movie.select('div.photo-info > span > date')[1].text
                movie_list.append(
                    {'movie_code': movie_code, 'movie_name': movie_name, 'release_date': movie_date, 'status': 0})
            return movie_list
        except Exception as e:
            logging.error(f'javbus获取演员影片列表失败，原因为{e}', exc_info=True)
            return None


class mteam_crawl:

    def __init__(self):
        self.cookie, self.ua, self.proxy, self.domain = get_mteam_conf()
        self.headers = {
            'cookie': self.cookie,
            'user-agent': self.ua,
            'Referer': "https://kp.m-team.cc",
        }
        self.proxies = {
            'http': self.proxy,
            'https': self.proxy,
        }

    def search_mteam(self, keyword):
        url = f'https://kp.m-team.cc/adult.php?incldead=1&spstate=0&inclbookmarked=0&search={keyword}&search_area=0&search_mode=0'

        dict_cookie = str_cookies_to_dict(self.cookie)
        response = requests.get(url, headers=self.headers, cookies=dict_cookie, proxies=self.proxies, timeout=30).text
        if 'cloudflare' in response:
            _LOGGER.error('可能遭遇CloudFlare五秒盾，一会再试试吧。')
            return False
        soup_tmp = SoupStrainer('table', {'class': 'torrents'})
        soup = BeautifulSoup(response, 'html.parser', parse_only=soup_tmp)
        trs = soup.select('table.torrents > tr:has(table.torrentname)')
        torrents = []
        for tr in trs:
            title = tr.select('a[title][href^="details.php?id="]')[0].get('title')
            download_url = tr.select('a[href^="download.php?id="]')[0].get('href')
            size = tr.select('td.rowfollow:nth-last-child(6)')[0].text
            seeders = tr.select('td.rowfollow:nth-last-child(5)')[0].text.replace(',', '')
            leechers = tr.select('td.rowfollow:nth-last-child(4)')[0].text.replace(',', '')
            grabs = tr.select('td.rowfollow:nth-last-child(3)')[0].text.replace(',', '')
            describe_list = tr.select('table.torrentname > tr > td.embedded')[0].contents
            describe = describe_list[len(describe_list) - 1].text
            img = tr.select('img[alt="torrent thumbnail"]')[0].get('src')
            torrent_rank = {
                'title': title,
                'download_url': download_url,
                'size': size,
                'seeders': seeders,
                'leechers': leechers,
                'grabs': grabs,
                'describe': describe,
                'img': img,
            }
            weight = get_weight(title, int(grabs), int(seeders), describe)
            torrent_rank['weight'] = weight
            torrents.append(torrent_rank)
        return torrents
