import re
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse, urlunparse

from stream2mediaserver.models.search_result import SearchResult
from stream2mediaserver.models.series import Series
from stream2mediaserver.processors.request_manager import RequestManager

import html
from urllib.parse import unquote

class SearchManager:

    @staticmethod
    def get_dle_login_hash(provider, url):
        response = RequestManager().get(url)
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_text = soup.find('script', text=re.compile(r'var dle_login_hash'))
            if script_text:
                match = re.search(r"var dle_login_hash = '(\w+)';", script_text.string)
                if match:
                    return match.group(1)
        return None

    @staticmethod
    def clean_text(text):
        text = html.unescape(text)
        text = text.replace('\r', '').replace('\n', '')
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def search_movies(provider, query, base_url, search_url):
        #TBD refactor to common calls, for now just ifs
        dle_hash = SearchManager.get_dle_login_hash(provider, base_url)
        
        if provider != "animeon":
            if not dle_hash:
                print("Failed to retrieve dle_login_hash")

        encoded_query = quote(query)
        
        #uakino dle
        if provider == "uakino":
            form_data = {
                'story': encoded_query,
                'dle_hash': dle_hash,
                'thisUrl': '/'
            }

            response = RequestManager.post(search_url, data=form_data)
            results = []
            if response.ok:
                soup = BeautifulSoup(response.json()['content'], 'html.parser')
                for link in soup.find_all('a', class_='search-result-link'):
                    url = unquote(link.get('href', ''))
                    poster = unquote(link.img.get('src', '')) if link.img else ''
                    if poster:
                        parsed_url = urlparse(poster)
                        if not parsed_url.netloc:
                            new_url = urlunparse(parsed_url._replace(scheme='https', netloc='uakino.club'))
                            poster = new_url
                    # Extracting and cleaning the name
                    name = link.find('span', class_='searchheading')
                    name = SearchManager.clean_text(name.get_text()) if name else ''

                    # Extracting and cleaning the English name
                    name_eng = link.find('span', class_='search-orig-title')
                    name_eng = SearchManager.clean_text(name_eng.get_text()) if name_eng else ''
                    results.append(SearchResult(link=url, image_url=poster, title=name, title_eng=name_eng, provider=provider))
            return results
        
        #anitube dle
        if provider == "anitube":
            form_data = {
                'query': query,
                'user_hash': dle_hash
            }

            response = RequestManager.post(search_url, data=form_data)
            results = []
            if response.ok:
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', style="display: block;"):
                    url = unquote(link.get('href', ''))
                    poster = unquote(link.img.get('src', '')) if link.img else ''

                    # Extracting and cleaning the name
                    name = link.find('b', class_='searchheading_title')
                    name = SearchManager.clean_text(name.get_text()) if name else ''

                    # Set English name to 'Not Specified' as there is no corresponding element
                    name_eng = 'Not Specified'

                    results.append(SearchResult(link=url, image_url=poster, title=name, title_eng=name_eng, provider=provider))
            return results

        #uaflix dle
        if provider == "uaflix":

            response = RequestManager.get(f'{search_url}{encoded_query}')
            results = []
            if response.ok:
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', class_='sres-wrap clearfix'):
                    url = unquote(link.get('href', ''))
                    poster = unquote(link.find('img').get('src', ''))
                    if not poster.startswith('http'):
                        poster = 'https://uaflix.net' + poster

                    # Extracting and cleaning the name
                    name = link.find('h2').get_text().split('/')[0].strip()

                    # Extracting and cleaning the English name
                    name_eng = link.find('h2').get_text().split('/')[1].strip() if '/' in link.find('h2').get_text() else 'Not Specified'

                    results.append(SearchResult(link=url, image_url=poster, title=name, title_eng=name_eng, provider=provider))
            return results
        
        #animeon custom json
        if provider == "animeon":

            response = RequestManager.get(f'{search_url}/{encoded_query}?full=false')
            results = []
            if response.ok:
                data = response.json()
                for item in data['result']:
                    url = f"https://animeon.club/api/anime/{item['id']}"
                    poster = ""
                    if item.get('poster'):
                        poster = item['poster']
                    elif item.get('image') and item['image'].get('original'):
                        poster = f"https://animeon.club/api/uploads/images/{item['image']['original']}"
                    elif item.get('image') and item['image'].get('preview'):
                        poster = f"https://animeon.club/api/uploads/images/{item['image']['preview']}"

                    # Extracting title in Ukrainian
                    name = item['titleUa']

                    # Extracting title in English
                    name_eng = item['titleEn']

                    results.append(SearchResult(link=url, image_url=poster, title=name, title_eng=name_eng, provider=provider))
            return results

    @staticmethod
    def get_series_page(series_url):
        response = RequestManager.get(series_url)
        if response.ok:
            series_list = []
            soup = BeautifulSoup(response.json()['response'], 'html.parser')
            for ul in soup.find_all('ul'):
                for li in ul.find_all('li', attrs={"data-id": True, "data-file": True}):
                    studio_id = li['data-id']
                    studio_name = li['data-voice']
                    series = li.text.strip()
                    video_url = f'https:{li["data-file"]}'
                    series_list.append(Series(studio_id, studio_name, series, video_url))
            return series_list
        return []

    @staticmethod
    def user_select_series(series_list):
        for index, series in enumerate(series_list):
            print(f"{index + 1}: {series.series} ({series.studio_name})")
        choice = int(input("Choose a series by number: ")) - 1
        return series_list[choice]

    @staticmethod
    def extract_id_from_url(url):
        match = re.search(r'/(\d+)-|/(\d+)\.html', url)
        if match:
            return match.group(1) if match.group(1) else match.group(2)
        return None