import os
from py3createtorrent import create_torrent


def create_torrents_for_folder(input_path, output_path):
    # Check if the input path exists
    if not os.path.exists(input_path):
        print(f"The specified input path does not exist: {input_path}")
        return

    # Check if the output path exists, if not, create it
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Iterate over each file in the input directory
    for filename in os.listdir(input_path):
        file_path = os.path.join(input_path, filename)

        # Check if it is a file (and not a directory)
        if os.path.isfile(file_path):
            # Create torrent file path
            torrent_path = os.path.join(output_path, f"{filename}.torrent")

            # Create the torrent file
            create_torrent(
                file_path,
                torrent_path,
                trackers=["udp://tracker.openbittorrent.com:80"],
            )

            print(f"Torrent created for: {file_path} at {torrent_path}")


# Example usage
input_folder = "/path/to/your/files"
output_folder = "/path/to/save/torrents"
create_torrents_for_folder(input_folder, output_folder)
