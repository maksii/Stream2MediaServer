"""MP4 file processing manager."""

import os
import re
import requests
from bs4 import BeautifulSoup
import m3u8

from ..utils.logger import logger
from .file_manager import FileManager
from .request_manager import RequestManager

class MP4Manager:
    @staticmethod
    def identify_best_quality(urls):
        quality_dict = {
            '360p': 1,
            '480p': 2,
            '720p': 3,
            '1080p': 4
        }
        best_quality = 0
        best_url = ''
        for url in urls:
            for quality in quality_dict:
                if f'[{quality}]' in url:
                    if quality_dict[quality] > best_quality:
                        best_quality = quality_dict[quality]
                        best_url = url.split(']')[1]
        return best_url
    
    @staticmethod
    def get_master_playlist(series_url):
        response = RequestManager.get(series_url)
        if response and response.ok:
            soup = BeautifulSoup(response.json()['response'], 'html.parser')
            scripts = soup.find_all('script')
            for script in scripts:
                if 'Playerjs' in script.text:
                    start = script.text.find('file:"') + 6
                    end = script.text.find('"}', start)
                    file_info = script.text[start:end]
                    urls = file_info.split(',')
                    return urls
        return None

    @staticmethod
    def download_series_content(series_url, destination, series_name):
    
        urls = MP4Manager.get_master_playlist(series_url)
        highest_quality_playlist = MP4Manager.identify_best_quality(urls)
    
        if highest_quality_playlist is None:
            raise Exception("No available streams found in the playlist")
    
        FileManager.download_file(highest_quality_playlist, destination, series_name)
    
        print("Download completed.")
        return None