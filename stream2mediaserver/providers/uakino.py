import os
import subprocess
import time
import m3u8
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

import urllib.request

class SearchResult:
    def __init__(self, url, poster, name, original_name):
        self.url = url
        self.poster = poster
        self.name = name
        self.original_name = original_name

    def __repr__(self):
        return f"SearchResult(url={self.url}, poster={self.poster}, name={self.name}, original_name={self.original_name})"

class Series:
    def __init__(self, studio_id, studio_name, series, url):
        self.studio_id = studio_id
        self.studio_name = studio_name
        self.series = series
        self.url = url

    def __repr__(self):
        return f"Series(studio_id={self.studio_id}, studio_name={self.studio_name}, series={self.series}, url={self.url})"

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

def get_master_playlist(series_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(series_url, headers=headers)
    if response.ok:
        # Regex to extract the file URL from the Playerjs configuration
        match = re.search(r'file:"(https[^"]+\.m3u8)"', response.text)
        if match:
            m3u8_url = match.group(1)
            print(f"Found m3u8 URL: {m3u8_url}")

            return m3u8_url
        else:
            print("No m3u8 URL found in the page.")
    else:
        print("Failed to load the series page.")
        
def download_series_content(m3u8_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    # Create media directory if it doesn't exist
    if not os.path.exists('media'):
        os.makedirs('media')
    
    # Load the master m3u8 file
    master_m3u8 = m3u8.load(m3u8_url)
    # Select the highest quality stream (first playlist in your case for 1080p as the last one)
    highest_quality_playlist_url = master_m3u8.playlists[-1].uri
    
    # Load the highest quality m3u8 file
    playlist_m3u8 = m3u8.load(highest_quality_playlist_url)
    # Find the highest bandwidth stream
    highest_bandwidth = 0
    highest_quality_playlist_url = None
    for playlist in master_m3u8.playlists:
        if playlist.stream_info.bandwidth > highest_bandwidth:
            highest_bandwidth = playlist.stream_info.bandwidth
            highest_quality_playlist_url = playlist.uri
    
    # Check if a highest quality stream was found
    if highest_quality_playlist_url is None:
        raise Exception("No available streams found in the playlist")
    
    # Load the highest quality m3u8 file
    playlist_m3u8 = m3u8.load(highest_quality_playlist_url)
    segment_base_url = highest_quality_playlist_url.rsplit('/', 1)[0] + '/'
    
    # Create media directory if it doesn't exist
    if not os.path.exists('media'):
        os.makedirs('media')
    
    segment_files = []
    # Download segments
    for segment in playlist_m3u8.segments:
        segment_url = segment.uri
        file_name = os.path.join('media', segment.uri.split('/')[-1])
        print(f"Downloading {segment_url} to {file_name}")
        segment_files.append(file_name)
        # Create request object with headers
        req = urllib.request.Request(segment_url, headers=headers)
        
        # Open the URL and read the data
        with urllib.request.urlopen(req) as response:
            data = response.read()
        
        # Write the data to a file
        with open(file_name, 'wb') as f:
            f.write(data)
    print("Download completed.")
    return segment_files

def concatenate_segmens_ts(segment_files, media_dir, filename):
    # Concatenate all segment files into a single file
    output_file_path = os.path.join(media_dir, f'{filename}.ts')
    with open(output_file_path, 'wb') as outfile:
        for segment_file in segment_files:
            with open(segment_file, 'rb') as readfile:
                outfile.write(readfile.read())

def concatenate_segmens_mvk(segment_files, media_dir, filename):
    # Create input.txt for FFmpeg
    input_txt_path = os.path.join(media_dir, 'input.txt')
    with open(input_txt_path, 'w') as f:
        for file in segment_files:
            f.write(f"file '{file}'\n")
    #TBD bug with path to files
    # Output file path
    output_file_path = os.path.join(media_dir, f'{filename}.mkv')
    
    # Use ffmpeg to concatenate and convert to MKV
    ffmpeg_command = ['ffmpeg', '-y', '-safe', '0', '-f', 'concat', '-i', input_txt_path, '-c', 'copy', output_file_path]
    with open('input.txt', 'w') as f:
        for file in segment_files:
            f.write(f"file '{file}'\n")
    
    subprocess.run(ffmpeg_command, check=True)


# Example usage
search_query = "The New Gate"
results = search_movies(search_query)
for index, result in enumerate(results):
    print(f"{index + 1}: {result.name} ({result.original_name})")
choice = int(input("Choose a result by number: ")) - 1
selected_result = results[choice]

selected_result_id = extract_id_from_url(selected_result.url)
series_list = get_series_page(selected_result_id)
selected_series = user_select_series(series_list)
print(f"You selected: {selected_series}")

m3u8_url = get_master_playlist(selected_series.url)
segment_files = download_series_content(m3u8_url)
media_dir = 'media'
filename = "aaa_test"
concatenate_segmens_ts(segment_files, media_dir, filename)
concatenate_segmens_mvk(segment_files, media_dir, filename)