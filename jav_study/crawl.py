import requests
import logging
from bs4 import BeautifulSoup, SoupStrainer

from moviebotapi.site import SearchType, SearchQuery, CateLevel1
from mbot.openapi import mbot_api

from .event import event_var
from .common import wait_for_mteam
from .torrent import get_weight

_LOGGER = logging.getLogger(__name__)
server = mbot_api


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
            _LOGGER.info(f'开始获取最受欢迎影片')
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
            logging.error(f'获取最受欢迎影片失败，原因为{e}', exc_info=True)
            return False

    def jav_search(self, keyword):
        from .common import set_true_code
        code = set_true_code(keyword)
        url = f'https://www.javlibrary.com/cn/vl_searchbyid.php?keyword={code}'
        result_list = []
        try:
            _LOGGER.info(f'开始在图书馆查询「{code}」')
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
            logging.error(f'图书馆搜索列表解析失败，原因为{e}', exc_info=True)
            return False

    def get_detail(self, soup):
        video_info = {}
        try:
            if '搜寻没有结果' in soup.text:
                _LOGGER.error(f'图书馆搜索列表解析失败，找不到任何结果')
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
                video_info['av_img'] = av_img
                return video_info
        except Exception as e:
            logging.error(f'图书馆详情页解析失败，原因为{e}', exc_info=True)
            return None


class javbus_crawl:
    def __init__(self):
        self.headers = event_var.headers
        self.proxies = event_var.proxies
        self.smms_token = event_var.smms_token
        self.hosts = [
            'https://www.javbus.com',
            'https://www.dmmbus.lol',
            'https://www.buscdn.lol',
            'https://www.busdmm.lol'
        ]

    def crawl_star_code(self, star):
        try:
            for host in self.hosts:
                url = f"{host}/searchstar/{star}"
                try:
                    r = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30, allow_redirects=False)
                    break
                except Exception as e:
                    continue
            if not r:
                _LOGGER.error(f"公交车搜索演员{star}失败")
                return None
            soup = BeautifulSoup(r.text, 'html.parser')
            stars = soup.select('a.avatar-box')
            # if len(stars) > 1:
            #     return None
            if len(stars) < 1:
                _LOGGER.error(f"找不到演员{star}的信息")
                return None
            url = stars[0].get('href')
            star_id = url.split('/')[-1]
            star_name = stars[0].select('div.photo-frame > img')[0].get('title')
            if event_var.smms_token:
                star_avatar = 'https://www.javbus.com' + stars[0].select('div.photo-frame > img')[0].get('src')
                avatar = self.save_avatar_and_upload(star_name, star_avatar)
                if avatar:
                    star_avatar = avatar["img_url"]
                    avatar_del_url = avatar["del_url"]
                else:
                    star_avatar = ''
                    avatar_del_url = ''
            else:
                star_avatar = ''
                avatar_del_url = ''
            star_detail = self.crawl_actor_detail(star_id)
            star_info = {
                "star_id": star_id, "star_name": star_name, "star_avatar": star_avatar,
                "del_avatar_img": avatar_del_url, "star_detail": star_detail}
            return star_info
        except Exception as e:
            logging.error(f'公交车搜索演员失败，原因为{e}', exc_info=True)
            return None

    def save_avatar_and_upload(self, star_name, star_avatar):
        import os
        try:
            avatar_img_path = '/data/plugins/jav_study/avatar_img/'
            if not os.path.exists(avatar_img_path):
                os.makedirs(avatar_img_path)
            if 'nowprinting.gif' in star_avatar:
                _LOGGER.error(f'「{star_name}」老师无头像。')
                return None
            try:
                r = requests.get(star_avatar, headers=self.headers, proxies=self.proxies, timeout=30)
            except Exception as e:
                _LOGGER.error(f'老师头像下载失败，错误信息{e}')
                return None
            if r.status_code == 200:
                with open(f'{avatar_img_path}{star_name}.jpg', 'wb') as f:
                    f.write(r.content)
                f.close()
            r = requests.post('https://sm.ms/api/v2/upload',
                              headers={'Authorization': self.smms_token},
                              files={'smfile': open(f'{avatar_img_path}{star_name}.jpg', 'rb')},
                              proxies=self.proxies, timeout=30).json()
            if r["success"]:
                img_url = r['data']['url']
                del_url = r['data']['delete']
                avatar = {
                    "img_url": img_url,
                    "del_url": del_url
                }
                return avatar
            else:
                _LOGGER.error(f'老师头像上传失败，错误信息{r["message"]}')
                return None
        except Exception as e:
            logging.error(f'公交车保存头像并上传失败，原因为{e}', exc_info=True)
            return None

    def crawl_actor_detail(self, star_id):
        try:
            for host in self.hosts:
                url = f"{host}/star/{star_id}"
                try:
                    r = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30, allow_redirects=False)
                    break
                except Exception as e:
                    continue
            if not r:
                return None
            soup = BeautifulSoup(r.text, 'html.parser')
            actor_details = soup.select('div.avatar-box > div.photo-info > p')
            content = []
            if actor_details:
                for item in actor_details:
                    content.append(item.text)
            return content
        except Exception as e:
            logging.error(f'公交车获取演员详情失败，原因为{e}', exc_info=True)
            return None

    def crawl_list_by_star(self, star_id):
        try:
            count = 1
            movie_list = []
            while True:
                url = f'https://www.javbus.com/star/{star_id}/{str(count)}'
                r = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30, allow_redirects=False)
                soup = BeautifulSoup(r.text, 'html.parser')
                pages = soup.select('ul.pagination > li')
                page = len(pages) - 1
                movies = soup.select('a.movie-box')
                for movie in movies:
                    movie_url = movie.get('href')
                    movie_name = movie.select('div.photo-info > span')[0].contents[0]
                    movie_code = movie.select('div.photo-info > span > date')[0].text
                    movie_date = movie.select('div.photo-info > span > date')[1].text
                    movie_actors = self.get_movie_actor(movie_url)
                    movie_list.append(
                        {"movie_code": movie_code, "movie_name": movie_name, "movie_url": movie_url,
                         "movie_actors": movie_actors, "release_date": movie_date, "status": 0})
                count += 1
                if count > page:
                    break
            return movie_list
        except Exception as e:
            logging.error(f'公交车获取演员影片列表失败，原因为{e}', exc_info=True)
            return None

    def get_movie_actor(self, url):
        try:
            r = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=30, allow_redirects=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            actors = soup.select('span.genre:has(a[href^="https://www.javbus.com/star/"])')
            actor_list = []
            for actor in actors:
                actor_url = actor.select('a')[0].get('href')
                actor_name = actor.select('a')[0].text
                actor_list.append({"actor_name": actor_name, "actor_url": actor_url})
            return actor_list
        except Exception as e:
            logging.error(f'公交车获取影片演员列表失败，原因为{e}', exc_info=True)
            return None

class site_torrent_crawl:

    def __init__(self):
        self.min_size = event_var.min_file_limit
        self.max_size = event_var.max_file_limit
        site_list = mbot_api.site.list()
        h_sites = ['mteam', 'pttime', 'hdbd', 'nicept']
        self.enable_site = [site.site_id for site in site_list if site.site_id in h_sites]

    def search_by_remote(self, keyword):
        try:
            _LOGGER.info(f'开始从站点搜索{keyword}...')
            query = SearchQuery(SearchType.Keyword, keyword)
            search_result = server.site.search_remote(query, [CateLevel1.AV], 15, self.enable_site)
            return search_result
        except Exception as e:
            logging.error(f'搜索{keyword}失败，错误信息：{e}', exc_info=True)
            return None

    def search_by_local(self, keyword):
        try:
            _LOGGER.info(f'开始从本地数据库搜索{keyword}...')
            query = SearchQuery(SearchType.Keyword, keyword)
            search_result = server.site.search_local(query, [CateLevel1.AV])
            return search_result
        except Exception as e:
            logging.error(f'搜索{keyword}失败，错误信息：{e}', exc_info=True)
            return None

    def search_by_keyword(self, keyword, task):
        try:
            if task == 'local':
                search_result = self.search_by_local(keyword)
            else:
                search_result = self.search_by_remote(keyword)
            torrents = []
            if search_result:
                for item in search_result:
                    torrent_id = item.id
                    site_id = item.site_id
                    name = item.name
                    size_mb = item.size_mb
                    size = str(size_mb) + 'MB' if size_mb < 1024 else str(round(size_mb / 1024, 2)) + 'GB'
                    poster_url = item.poster_url
                    subject = item.subject
                    download_url = item.download_url
                    download_count = item.download_count
                    upload_count = item.upload_count
                    torrent_rank = {
                        "torrent_id": torrent_id,
                        "site_id": site_id,
                        "name": name,
                        "subject": subject,
                        "size": size,
                        "poster_url": poster_url,
                        "download_url": download_url,
                        "download_count": download_count,
                        "upload_count": upload_count,
                    }
                    weight = get_weight(torrent_rank, self.min_size, self.max_size)
                    torrent_rank["weight"] = weight
                    torrents.append(torrent_rank)
                return torrents
            else:
                if task == 'remote':
                    _LOGGER.error(f'站点搜索{keyword}无结果，注意搜索频率，避免馒头限流。')
                    # wait_for_mteam()
                return None
        except Exception as e:
            logging.error(f'搜索种子出错，错误信息：{e}', exc_info=True)
            return None
