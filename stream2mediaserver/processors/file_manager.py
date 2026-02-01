import os
import urllib.request

from ..utils.logger import logger


class FileManager:
    @staticmethod
    def download_file(url, destination_folder, file_name):
        if not os.path.exists(destination_folder):
            os.makedirs(
                destination_folder, exist_ok=True
            )  # Use exist_ok to avoid race conditions
        file_path = os.path.join(destination_folder, file_name)
        req = urllib.request.Request(url)
        try:
            with (
                urllib.request.urlopen(req) as response,
                open(file_path, "wb") as out_file,
            ):
                out_file.write(response.read())
        except urllib.error.URLError as e:
            logger.error(f"Failed to download the file from {url}. Error: {e}")
            return None
        return file_path

    @staticmethod
    def concatenate_files(segment_files, output_file):
        try:
            with open(output_file, "wb") as outfile:
                for segment_file in segment_files:
                    with open(segment_file, "rb") as readfile:
                        outfile.write(readfile.read())
        except IOError as e:
            logger.error(f"Error during file concatenation. Error: {e}")
            return None
        return output_file
