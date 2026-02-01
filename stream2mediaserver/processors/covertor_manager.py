import subprocess


class ConvertorManager:
    def create_input_file_for_concatenation(self, segment_files, input_txt_path):
        with open(input_txt_path, "w") as f:
            for file in segment_files:
                f.write(f"file '{file}'\n")

    def concatenate_to_mkv(self, input_txt_path, output_file_path):
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-safe",
            "0",
            "-f",
            "concat",
            "-i",
            input_txt_path,
            "-c",
            "copy",
            output_file_path,
        ]
        try:
            subprocess.run(
                ffmpeg_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error during video concatenation: {e.stderr.decode()}")
            return False
        return True
