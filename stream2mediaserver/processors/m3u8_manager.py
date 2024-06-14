import os
import re
import m3u8
import requests

from processors.request_manager import RequestManager

class M3U8Manager:
    @staticmethod
    def load_m3u8(url, headers=None):
        headers = headers if headers is not None else {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        return m3u8.load(url, headers=headers)

    @staticmethod
    def get_best_quality_playlist(master_m3u8):
        highest_bandwidth = 0
        highest_quality_playlist = None
        for playlist in master_m3u8.playlists:
            if playlist.stream_info.bandwidth > highest_bandwidth:
                highest_bandwidth = playlist.stream_info.bandwidth
                highest_quality_playlist = playlist
        return highest_quality_playlist
    
@staticmethod
def get_master_playlist(series_url):
    response = RequestManager.get(series_url)
    if response and response.ok:
        match = re.search(r'file:"(https[^"]+\.m3u8)"', response.text)
        if match:
            m3u8_url = match.group(1)
            print(f"Found m3u8 URL: {m3u8_url}")
            return m3u8_url
        else:
            print("No m3u8 URL found in the page.")
    else:
        print("Failed to load the series page.")
        
@staticmethod
def download_series_content(m3u8_url):
    if not os.path.exists('media'):
        os.makedirs('media')

    master_m3u8 = M3U8Manager.load_m3u8(m3u8_url)
    highest_quality_playlist = M3U8Manager.get_best_quality_playlist(master_m3u8)

    if highest_quality_playlist is None:
        raise Exception("No available streams found in the playlist")

    playlist_m3u8 = M3U8Manager.load_m3u8(highest_quality_playlist.uri)
    segment_files = []

    for segment in playlist_m3u8.segments:
        segment_url = segment.absolute_uri
        file_name = os.path.join('media', segment_url.split('/')[-1])
        print(f"Downloading {segment_url} to {file_name}")
        segment_files.append(file_name)
        response = RequestManager.get(segment_url)

        if response.ok:
            with open(file_name, 'wb') as f:
                f.write(response.content)
        else:
            print(f"Failed to download segment: {segment_url}")

    print("Download completed.")
    return segment_files