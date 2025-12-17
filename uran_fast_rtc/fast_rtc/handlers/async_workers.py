"""
异步任务工作模块

为WebRTC Handler提供高性能的异步任务处理能力，包括：
- 视频录制异步worker
- 音频录制异步worker
- 抽帧保存异步worker

设计思路：
使用生产者-消费者模式，将耗时的I/O操作从主流程中解耦，
通过异步队列进行缓冲，使用线程池执行实际的I/O操作。
"""

import asyncio
import logging
import time
from typing import List, Optional, Tuple
import numpy as np
import cv2
import soundfile as sf
from PIL import Image

from constants import AsyncTaskConstants
from config import video_frames_dir_path, record_audio_dir_path
import os

logger = logging.getLogger("uran_fast_rtc")


class VideoRecordingWorker:
    """视频录制异步工作任务"""

    @staticmethod
    async def run(
        queue: asyncio.Queue,
        video_writer: cv2.VideoWriter,
        connection_id: int,
        stats: dict,
        get_enabled_func,
        resolution: Tuple[int, int],
    ):
        """
        视频录制工作循环

        Args:
            queue: 视频帧队列
            video_writer: CV2视频写入器
            connection_id: 连接ID
            stats: 统计信息字典
            get_enabled_func: 获取是否还在录制的回调
            resolution: 目标视频分辨率 (width, height)
        """
        logger.info(f"[连接 {connection_id}] 视频录制worker已启动")
        frames_written = 0

        try:
            while get_enabled_func() or not queue.empty():
                frames_batch = []

                # 批量获取帧（提高效率）
                for _ in range(AsyncTaskConstants.VIDEO_BATCH_SIZE):
                    try:
                        frame = queue.get_nowait()
                        frames_batch.append(frame)
                    except asyncio.QueueEmpty:
                        break

                # 批量写入（使用线程池避免阻塞）
                if frames_batch:
                    written = await asyncio.to_thread(
                        VideoRecordingWorker._write_frames_sync,
                        video_writer,
                        frames_batch,
                        resolution,
                    )
                    frames_written += written
                else:
                    # 没有帧，短暂休眠避免空转
                    await asyncio.sleep(AsyncTaskConstants.WORKER_POLL_INTERVAL)

            logger.info(
                f"[连接 {connection_id}] 视频录制worker完成，共写入 {frames_written} 帧"
            )

        except asyncio.CancelledError:
            logger.info(
                f"[连接 {connection_id}] 视频录制worker被取消，已写入 {frames_written} 帧"
            )
            raise
        except Exception as e:
            logger.error(f"[连接 {connection_id}] 视频录制worker异常: {e}")
            raise

    @staticmethod
    def _write_frames_sync(
        video_writer: cv2.VideoWriter,
        frames: List[np.ndarray],
        resolution: Tuple[int, int],
    ) -> int:
        """在独立线程中批量写入视频帧"""
        written = 0
        if not frames:
            return 0

        target_width, target_height = resolution

        # 简单的防卫性检查
        if target_width <= 0 or target_height <= 0:
            logger.error(f"无效的目标分辨率: {resolution}，跳过写入")
            return 0

        for frame in frames:
            try:
                # 移除颜色转换，假设输入已经是 BGR (或者让 OpenCV 处理)

                # 2. 处理分辨率不匹配
                h, w = frame.shape[:2]
                if w != target_width or h != target_height:
                    frame = cv2.resize(frame, (target_width, target_height))

                video_writer.write(frame)
                written += 1
            except Exception as e:
                logger.error(f"写入视频帧失败: {e}")
        return written


class AudioRecordingWorker:
    """音频录制异步工作任务"""

    @staticmethod
    async def run(
        queue: asyncio.Queue, connection_id: int, sample_rate: int, filepath: str
    ) -> int:
        """
        音频录制工作循环

        Args:
            queue: 音频帧队列
            connection_id: 连接ID
            sample_rate: 采样率
            filepath: 保存路径

        Returns:
            录制的帧数
        """
        logger.info(f"[连接 {connection_id}] 音频录制worker已启动")
        recorded_frames = []

        try:
            while True:
                try:
                    audio_data = await asyncio.wait_for(
                        queue.get(), timeout=AsyncTaskConstants.QUEUE_GET_TIMEOUT
                    )
                    recorded_frames.append(audio_data)
                except asyncio.TimeoutError:
                    # 超时说明没有新数据了，录制结束
                    break

            # 保存音频文件
            if recorded_frames:
                frame_count = len(recorded_frames)
                await asyncio.to_thread(
                    AudioRecordingWorker._save_audio_sync,
                    recorded_frames,
                    sample_rate,
                    filepath,
                )
                logger.info(
                    f"[连接 {connection_id}] 音频录制worker完成，共 {frame_count} 帧"
                )
                return frame_count
            else:
                logger.warning(f"[连接 {connection_id}] 音频录制worker结束，无帧可保存")
                return 0

        except asyncio.CancelledError:
            logger.info(f"[连接 {connection_id}] 音频录制worker被取消")
            raise
        except Exception as e:
            logger.error(f"[连接 {connection_id}] 音频录制worker异常: {e}")
            raise

    @staticmethod
    def _save_audio_sync(frames: List[np.ndarray], sample_rate: int, filepath: str):
        """在独立线程中保存音频文件"""
        full_audio = np.concatenate(frames)
        sf.write(filepath, full_audio, sample_rate)
        logger.info(f"录音已保存到 {filepath}")


class FrameSaveWorker:
    """抽帧保存异步工作任务"""

    @staticmethod
    async def run(
        queue: asyncio.Queue,
        connection_id: int,
        get_enabled_func,
        get_count_func,
        increment_count_func,
        filepath: str
    ):
        """
        抽帧保存工作循环

        Args:
            queue: 帧队列
            connection_id: 连接ID
            get_enabled_func: 获取是否还在抽帧的回调
            get_count_func: 获取当前帧count的回调
            increment_count_func: 递增count的回调
            filepath: 抽帧数据存放路径
        """
        logger.info(f"[连接 {connection_id}] 抽帧保存worker已启动")
        saved_count = 0

        try:
            while get_enabled_func() or not queue.empty():
                try:
                    frame = await asyncio.wait_for(
                        queue.get(), timeout=AsyncTaskConstants.QUEUE_GET_TIMEOUT
                    )

                    # 异步保存帧
                    await asyncio.to_thread(
                        FrameSaveWorker._save_frame_sync,
                        frame,
                        get_count_func(),
                        connection_id,
                        filepath
                    )

                    increment_count_func()
                    saved_count += 1

                except asyncio.TimeoutError:
                    # 超时，继续等待
                    continue

            logger.info(
                f"[连接 {connection_id}] 抽帧保存worker完成，共保存 {saved_count} 帧"
            )

        except asyncio.CancelledError:
            logger.info(f"[连接 {connection_id}] 抽帧保存worker被取消")
            raise
        except Exception as e:
            logger.error(f"[连接 {connection_id}] 抽帧保存worker异常: {e}")
            raise

    @staticmethod
    def _save_frame_sync(frame: np.ndarray, frame_number: int, connection_id: int, filepath: str):
        """在独立线程中保存视频帧"""
        try:
            # WebRTC/aiortc 传入的帧是 BGR 格式，PIL 期望 RGB 格式，需要转换
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                # BGRA -> RGBA
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGBA)
                image = Image.fromarray(frame_rgb.astype("uint8"), mode="RGBA")
            elif len(frame.shape) == 3 and frame.shape[2] == 3:
                # BGR -> RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb.astype("uint8"), mode="RGB")
            else:
                image = Image.fromarray(frame.astype("uint8"), mode="L")

            # 生成文件名并保存
            timestamp = int(time.time())
            filename = f"frame_{timestamp}_{frame_number:04d}.png"
            image.save(filepath)

            logger.info(
                f"[连接 {connection_id}] 视频帧已保存: {filename} (第 {frame_number + 1} 帧)"
            )

        except Exception as e:
            logger.error(f"[连接 {connection_id}] 保存视频帧失败: {e}")
