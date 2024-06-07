import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

class SearchManager:
    
    def get_dle_login_hash():
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get("https://uakino.club", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_text = soup.find('script', text=re.compile(r'var dle_login_hash'))
        if script_text:
            match = re.search(r"var dle_login_hash = '(\w+)';", script_text.string)
            if match:
                return match.group(1)
        return None
    
    def search_movies(query):
        dle_hash = get_dle_login_hash()
        if not dle_hash:
            print("Failed to retrieve dle_login_hash")
            return []

        encoded_query = quote(query)
        form_data = {
            'story': encoded_query,
            'dle_hash': dle_hash,
            'thisUrl': '/'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.post("https://uakino.club/engine/lazydev/dle_search/ajax.php", data=form_data, headers=headers)
        results = []
        if response.ok:
            soup = BeautifulSoup(response.json()['content'], 'html.parser')
            for link in soup.find_all('a', class_='search-result-link'):
                url = link['href']
                poster = link.find('img', class_='search-poster')['src']
                name = " ".join(link.find('span', class_='searchheading').text.strip().split())
                original_name = link.find('span', class_='search-orig-title').text.strip()
                results.append(SearchResult(url, poster, name, original_name))
        return results

    def get_series_page(news_id):
        timestamp = int(time.time())
        url = f"https://uakino.club/engine/ajax/playlists.php?news_id={news_id}&xfield=playlist&time={timestamp}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.ok:
            series_list = []
            soup = BeautifulSoup(response.json()['response'], 'html.parser')
            for ul in soup.find_all('ul'):
                for li in ul.find_all('li', attrs={"data-id": True, "data-file": True}):
                    studio_id = li['data-id']
                    studio_name = li['data-voice']
                    series = li.text
                    video_url = f'https:{li['data-file']}'
                    series_list.append(Series(studio_id, studio_name, series, video_url))
            return series_list
        return []

    def user_select_series(series_list):
        for index, series in enumerate(series_list):
            print(f"{index + 1}: {series.series} ({series.studio_name})")
        choice = int(input("Choose a series by number: ")) - 1
        return series_list[choice]

    def extract_id_from_url(url):
        match = re.search(r'/(\d+)-|/(\d+)\.html', url)
        if match:
            return match.group(1) if match.group(1) else match.group(2)
        return None