import m3u8

class M3U8Manager:
    def load_m3u8(self, url):
        return m3u8.load(url)

    def get_best_quality_playlist(self, master_m3u8):
        highest_bandwidth = 0
        highest_quality_playlist = None
        for playlist in master_m3u8.playlists:
            if playlist.stream_info.bandwidth > highest_bandwidth:
                highest_bandwidth = playlist.stream_info.bandwidth
                highest_quality_playlist = playlist
        return highest_quality_playlist

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