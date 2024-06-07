import os
import urllib.request

class FileManager:
    def download_file(self, url, destination_folder, file_name):
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        file_path = os.path.join(destination_folder, file_name)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
            out_file.write(response.read())
        return file_path

    def concatenate_files(self, segment_files, output_file):
        with open(output_file, 'wb') as outfile:
            for segment_file in segment_files:
                with open(segment_file, 'rb') as readfile:
                    outfile.write(readfile.read())