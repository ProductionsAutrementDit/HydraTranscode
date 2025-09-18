import asyncio
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Callable, Optional

logger = logging.getLogger(__name__)

class TranscodeTask:
    def __init__(
        self,
        task_id: str,
        input_files: List[str],
        output_settings: Dict,
        progress_callback: Callable,
        completion_callback: Callable,
        error_callback: Callable
    ):
        self.task_id = task_id
        self.input_files = input_files
        self.output_settings = output_settings
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
        self.process = None
        self.cancelled = False
        self.total_duration = None

    async def run(self):
        """Run the transcoding task"""
        try:
            # Validate input files exist
            for input_file in self.input_files:
                if not os.path.exists(input_file):
                    raise FileNotFoundError(f"Input file not found: {input_file}")

            # Create output directory if needed
            output_path = Path(self.output_settings['path'])
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build ffmpeg command
            cmd = self._build_ffmpeg_command()
            logger.info(f"Running ffmpeg command: {' '.join(cmd)}")

            # Get total duration for progress calculation
            self.total_duration = await self._get_total_duration()
            logger.info(f"Total duration: {self.total_duration} seconds")

            # Run ffmpeg with progress monitoring
            await self._run_ffmpeg(cmd)

            if not self.cancelled:
                await self.completion_callback(self.task_id)

        except Exception as e:
            logger.error(f"Transcoding error: {e}")
            await self.error_callback(self.task_id, str(e))

    async def cancel(self):
        """Cancel the transcoding task"""
        self.cancelled = True
        if self.process:
            self.process.terminate()
            await self.process.wait()

    def _detect_stream_type(self, file_path: str) -> dict:
        """Detect if file has video and/or audio streams"""
        # Check for video streams
        video_cmd = [
            'ffprobe', '-v', 'error', '-show_streams',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_type',
            '-of', 'json', file_path
        ]

        # Check for audio streams
        audio_cmd = [
            'ffprobe', '-v', 'error', '-show_streams',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_type',
            '-of', 'json', file_path
        ]

        has_video = False
        has_audio = False

        try:
            # Check video
            result = subprocess.run(video_cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            has_video = len(data.get('streams', [])) > 0
        except subprocess.CalledProcessError:
            # No video stream
            has_video = False
        except Exception as e:
            logger.warning(f"Error detecting video stream for {file_path}: {e}")

        try:
            # Check audio
            result = subprocess.run(audio_cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            has_audio = len(data.get('streams', [])) > 0
        except subprocess.CalledProcessError:
            # No audio stream
            has_audio = False
        except Exception as e:
            logger.warning(f"Error detecting audio stream for {file_path}: {e}")

        logger.info(f"Stream detection for {file_path}: video={has_video}, audio={has_audio}")
        return {'video': has_video, 'audio': has_audio}

    def _build_ffmpeg_command(self) -> List[str]:
        """Build ffmpeg command for transcoding"""
        cmd = ['ffmpeg', '-y']  # -y to overwrite output

        # Detect stream types for each input
        stream_info = []
        video_files = []
        audio_files = []

        for i, input_file in enumerate(self.input_files):
            info = self._detect_stream_type(input_file)
            stream_info.append(info)

            if info['video']:
                video_files.append((i, input_file))
            elif info['audio']:
                audio_files.append((i, input_file))

        # Add input files
        for input_file in self.input_files:
            cmd.extend(['-i', input_file])

        # Handle multiple inputs
        if len(self.input_files) > 1:
            filter_parts = []
            map_commands = []

            if len(video_files) > 1:
                # Normalize and concatenate video files
                # First, scale and format all videos to be compatible
                normalized_videos = []
                normalized_audios = []

                target_resolution = self.output_settings.get('resolution', '1920x1080')

                for i, (idx, _) in enumerate(video_files):
                    # Normalize each video stream to same format
                    # Use simpler filter chain without complex expressions
                    width, height = target_resolution.split('x')
                    filter_parts.append(
                        f"[{idx}:v]"
                        f"scale=w={width}:h={height}:force_original_aspect_ratio=decrease,"
                        f"pad={width}:{height}:-1:-1:color=black,"
                        f"setsar=1,"
                        f"fps=30,"
                        f"format=yuv420p"
                        f"[v{i}]"
                    )
                    normalized_videos.append(f"[v{i}]")

                    # Handle audio if present
                    if stream_info[idx]['audio']:
                        normalized_audios.append(f"[{idx}:a]")

                # Concatenate normalized video streams
                video_concat = ''.join(normalized_videos)
                filter_parts.append(f"{video_concat}concat=n={len(video_files)}:v=1:a=0[outv]")

                # Concatenate audio streams if any
                if normalized_audios:
                    audio_concat = ''.join(normalized_audios)
                    filter_parts.append(f"{audio_concat}concat=n={len(normalized_audios)}:v=0:a=1[outa_main]")
                    map_commands.extend(['-map', '[outa_main]'])

                map_commands.insert(0, '[outv]')
                map_commands.insert(0, '-map')
            elif len(video_files) == 1:
                # Single video file, just map it
                idx, _ = video_files[0]
                map_commands.extend(['-map', f'{idx}:v'])
                if stream_info[idx]['audio']:
                    map_commands.extend(['-map', f'{idx}:a'])

            # Add additional audio files as separate tracks
            for idx, audio_file in audio_files:
                map_commands.extend(['-map', f'{idx}:a'])

            if filter_parts:
                cmd.extend(['-filter_complex', ';'.join(filter_parts)])

            cmd.extend(map_commands)
        else:
            # Single input, just process normally
            if stream_info[0]['video']:
                cmd.extend(['-map', '0:v'])
            if stream_info[0]['audio']:
                cmd.extend(['-map', '0:a'])

        # Add output settings
        codec = self.output_settings.get('codec', 'h264')
        resolution = self.output_settings.get('resolution')

        # Video codec
        if codec == 'h264':
            cmd.extend(['-c:v', 'libx264', '-preset', 'medium'])
        elif codec == 'h265':
            cmd.extend(['-c:v', 'libx265', '-preset', 'medium'])
        elif codec == 'vp9':
            cmd.extend(['-c:v', 'libvpx-vp9'])

        # Resolution - only apply if not using filter complex (filters already handle it)
        if resolution and len(self.input_files) == 1:
            cmd.extend(['-s', resolution])

        # Audio codec (AAC for MVP)
        cmd.extend(['-c:a', 'aac'])

        # Progress stats
        cmd.extend(['-progress', 'pipe:1', '-stats'])

        # Output file
        cmd.append(self.output_settings['path'])

        return cmd

    async def _get_total_duration(self) -> float:
        """Get total duration of all input files"""
        total = 0.0
        for input_file in self.input_files:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                input_file
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                duration = float(result.stdout.strip())
                total += duration
            except Exception as e:
                logger.warning(f"Could not get duration for {input_file}: {e}")

        return total if total > 0 else 1.0  # Avoid division by zero

    async def _run_ffmpeg(self, cmd: List[str]):
        """Run ffmpeg and monitor progress"""
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        last_progress = 0
        progress_pattern = re.compile(r'out_time_ms=(\d+)')

        async def read_progress():
            nonlocal last_progress
            async for line in self.process.stdout:
                if self.cancelled:
                    break

                line_str = line.decode('utf-8', errors='ignore')

                # Parse progress from ffmpeg stats
                match = progress_pattern.search(line_str)
                if match:
                    time_ms = int(match.group(1))
                    time_seconds = time_ms / 1_000_000

                    if self.total_duration > 0:
                        progress = min((time_seconds / self.total_duration) * 100, 99.9)
                        # Only send update if progress changed significantly
                        if progress - last_progress >= 1.0:
                            await self.progress_callback(self.task_id, progress)
                            last_progress = progress

        async def read_stderr():
            async for line in self.process.stderr:
                line_str = line.decode('utf-8', errors='ignore')
                if 'error' in line_str.lower():
                    logger.error(f"FFmpeg error: {line_str}")

        # Read both stdout and stderr concurrently
        await asyncio.gather(
            read_progress(),
            read_stderr(),
            return_exceptions=True
        )

        # Wait for process to complete
        return_code = await self.process.wait()

        if return_code != 0 and not self.cancelled:
            raise RuntimeError(f"FFmpeg failed with return code {return_code}")