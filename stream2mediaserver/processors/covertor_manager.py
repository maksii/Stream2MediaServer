from pathlib import Path
import subprocess
from typing import Iterable, Optional

from ..config import AppConfig
from ..models.series import Series
from ..utils.logger import logger


class ConvertorManager:
    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self.config = config

    @staticmethod
    def create_input_file_for_concatenation(
        segment_files: Iterable[str], input_txt_path: str
    ) -> None:
        Path(input_txt_path).parent.mkdir(parents=True, exist_ok=True)
        with open(input_txt_path, "w", encoding="utf-8") as f:
            for file in segment_files:
                f.write(f"file '{file}'\n")

    @staticmethod
    def concatenate_to_mkv(input_txt_path: str, output_file_path: str) -> bool:
        ffmpeg_command = ConvertorManager._build_concat_command(
            input_txt_path, output_file_path
        )
        try:
            subprocess.run(
                ffmpeg_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                "Error during video concatenation: %s", e.stderr.decode("utf-8")
            )
            return False
        return True

    @staticmethod
    def concatenate_segments_ts(
        segment_files: Iterable[str],
        media_dir: str = "media",
        filename: str = "final_output",
    ) -> Optional[str]:
        return ConvertorManager._concatenate(segment_files, media_dir, filename, "ts")

    @staticmethod
    def concatenate_segments_mvk(
        segment_files: Iterable[str],
        media_dir: str = "media",
        filename: str = "final_output",
    ) -> Optional[str]:
        return ConvertorManager._concatenate(segment_files, media_dir, filename, "mkv")

    @staticmethod
    def concatenate_segmens_ts(
        segment_files: Iterable[str],
        media_dir: str = "media",
        filename: str = "final_output",
    ) -> Optional[str]:
        return ConvertorManager.concatenate_segments_ts(
            segment_files, media_dir, filename
        )

    @staticmethod
    def concatenate_segmens_mvk(
        segment_files: Iterable[str],
        media_dir: str = "media",
        filename: str = "final_output",
    ) -> Optional[str]:
        return ConvertorManager.concatenate_segments_mvk(
            segment_files, media_dir, filename
        )

    def process(self, item: Series) -> bool:
        logger.warning("ConvertorManager.process is not configured for item: %s", item)
        return False

    @staticmethod
    def _build_concat_command(input_txt_path: str, output_file_path: str) -> list[str]:
        return [
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

    @staticmethod
    def _concatenate(
        segment_files: Iterable[str],
        media_dir: str,
        filename: str,
        extension: str,
    ) -> Optional[str]:
        if not segment_files:
            logger.error("No segment files provided for concatenation.")
            return None
        output_dir = Path(media_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{filename}.{extension}"
        input_txt_path = output_dir / f"{filename}_input.txt"
        ConvertorManager.create_input_file_for_concatenation(
            segment_files, str(input_txt_path)
        )
        if ConvertorManager.concatenate_to_mkv(str(input_txt_path), str(output_file)):
            return str(output_file)
        return None
