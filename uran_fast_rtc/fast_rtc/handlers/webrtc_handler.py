"""
WebRTC Handler 业务逻辑模块

负责处理 WebRTC 音视频流的核心业务逻辑，包括：
- 音频接收、发送、录制与回放
- 视频接收、发送、抽帧与录制
- DataChannel 消息处理
- 连接生命周期管理
"""

import asyncio
import json
import logging
import os
import time
from typing import Tuple, List, Optional
import numpy as np
import cv2
from fastrtc import (
    AsyncAudioVideoStreamHandler,
    AudioEmitType,
    VideoEmitType,
    wait_for_item,
)

from constants import (
    StreamMode,
    MessageType,
    VideoCodec,
    VideoConstants,
    AudioConstants,
    AsyncTaskConstants,
)

from config import (
    record_audio_dir_path,
    video_frames_dir_path,
    video_recordings_dir_path,
)

logger = logging.getLogger("uran_fast_rtc")


class UranEchoHandler(AsyncAudioVideoStreamHandler):
    """
    WebRTC 音视频流处理器

    提供音视频的接收、发送、录制等完整功能。
    """

    def __init__(
        self, expected_layout="mono", output_sample_rate=24000, output_frame_size=480
    ) -> None:
        super().__init__(
            expected_layout,
            output_sample_rate,
            output_frame_size,
            input_sample_rate=16000,
        )
        self.start_time = None
        self.connection_id = None
        self.video_queue = asyncio.Queue()
        self.audio_queue = asyncio.Queue()

        # 状态管理
        self.mode = StreamMode.LIVE  # 音频流模式
        self.recorded_audio_frames: List[np.ndarray] = []
        self.replay_index = 0
        self.sample_rate = AudioConstants.INPUT_SAMPLE_RATE  # 输入采样率

        # 视频抽帧相关
        self.frame_capture_enabled = False
        self.latest_video_frame: Optional[np.ndarray] = None
        self.video_resolution: Optional[Tuple[int, int]] = None  # (width, height)
        self.frame_capture_task: Optional[asyncio.Task] = None
        self.frame_count = 0
        self.total_frames_received = 0  # 总接收帧数

        # 视频录制相关
        self.video_recording_enabled = False
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.video_recording_path: Optional[str] = None
        self.recorded_video_frames = 0

        # ============ 异步任务架构 ============

        # 视频录制异步队列和任务
        self.video_recording_queue = asyncio.Queue(
            maxsize=AsyncTaskConstants.VIDEO_RECORDING_QUEUE_SIZE
        )
        self.video_recording_worker_task: Optional[asyncio.Task] = None

        # 音频录制异步队列和任务
        self.audio_recording_queue = asyncio.Queue(
            maxsize=AsyncTaskConstants.AUDIO_RECORDING_QUEUE_SIZE
        )
        self.audio_recording_worker_task: Optional[asyncio.Task] = None

        # 抽帧保存异步队列和任务
        self.frame_save_queue = asyncio.Queue(
            maxsize=AsyncTaskConstants.FRAME_SAVE_QUEUE_SIZE
        )
        self.frame_save_worker_task: Optional[asyncio.Task] = None

        # 性能统计
        self.stats = {
            "video_dropped_frames": 0,
            "audio_dropped_frames": 0,
            "frame_save_dropped": 0,
            "video_queue_max_size": 0,
            "audio_queue_max_size": 0,
        }

        # 测试数据存储（用于 set_input 测试）
        self.input_data = {}  # 存储通过 set_input 传递的测试数据

    async def start_up(self):
        """连接建立时调用。"""
        self.connection_id = id(self)
        self.start_time = time.time()

        logger.info(f"[连接 {self.connection_id}] WebRTC 连接已建立")
        logger.info(
            f"[连接 {self.connection_id}] 连接时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}"
        )

        if self.channel:
            # 将 text_receive 方法绑定到通道的消息事件
            self.channel.add_listener("message", self.text_receive)
            logger.info(f"[连接 {self.connection_id}] DataChannel 消息监听器已绑定")

    async def shutdown(self):
        """连接断开时由框架调用，清理资源。"""
        logger.info(f"[连接 {self.connection_id}] WebRTC 连接正在断开")

        # 停止抽帧任务
        if self.frame_capture_enabled:
            self.stop_frame_capture()

        # 停止视频录制
        if self.video_recording_enabled:
            await self._stop_video_recording_async()

        # 停止音频录制
        if self.mode == StreamMode.RECORDING:
            await self._stop_audio_recording_async()

        # 等待所有异步任务完成
        await self._shutdown_async_workers()

        # 记录统计信息
        logger.info(
            f"[连接 {self.connection_id}] 统计：总接收视频帧 {self.total_frames_received} 帧，"
            f"抽帧保存 {self.frame_count} 帧，视频录制 {self.recorded_video_frames} 帧"
        )
        logger.info(
            f"[连接 {self.connection_id}] 性能统计："
            f"视频丢帧 {self.stats['video_dropped_frames']}，"
            f"音频丢帧 {self.stats['audio_dropped_frames']}，"
            f"抽帧丢弃 {self.stats['frame_save_dropped']}"
        )
        logger.info(f"[连接 {self.connection_id}] 连接已关闭")

    async def _shutdown_async_workers(self):
        """优雅关闭所有异步工作任务"""
        tasks_to_cancel = []

        # 收集需要取消的任务
        if self.video_recording_worker_task:
            tasks_to_cancel.append(("视频录制", self.video_recording_worker_task))
        if self.audio_recording_worker_task:
            tasks_to_cancel.append(("音频录制", self.audio_recording_worker_task))
        if self.frame_save_worker_task:
            tasks_to_cancel.append(("抽帧保存", self.frame_save_worker_task))

        # 等待队列清空（带超时）
        start_time = time.time()
        while time.time() - start_time < AsyncTaskConstants.SHUTDOWN_WAIT_TIMEOUT:
            all_empty = (
                self.video_recording_queue.empty()
                and self.audio_recording_queue.empty()
                and self.frame_save_queue.empty()
            )
            # 回放逻辑
            if self.replay_index < len(self.recorded_audio_frames):
                audio_data = self.recorded_audio_frames[self.replay_index]
                self.replay_index += 1

                # 排空实时队列以防止堆积，但不发送它
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                return self.sample_rate, audio_data
            else:
                # 回放结束
                logger.info(f"回放结束，切换回 {StreamMode.LIVE.description} 模式")
                self.mode = StreamMode.LIVE
                self.replay_index = 0
                if self.channel:
                    self.channel.send(
                        json.dumps(
                            {"type": MessageType.STATUS.value, "message": "回放结束"}
                        )
                    )

        # LIVE 或 RECORDING 模式：回声实时音频
        return await wait_for_item(self.audio_queue)

    def set_args(self, args: list):
        """
        接收通过 stream.set_input() 传递的参数（测试用）

        Args:
            args: 参数列表，可以是任意类型的数据
        """
        logger.info(f"[连接 {self.connection_id}] 接收到 set_input 数据: {args}")

        if not args:
            return

        # 情况 1: 传递的是字典
        if len(args) == 1 and isinstance(args[0], dict):
            self.input_data.update(args[0])
            logger.info(
                f"[连接 {self.connection_id}] 测试数据已更新: {self.input_data}"
            )

        # 情况 2: 传递的是字符串或其他类型
        else:
            self.input_data["last_input"] = args
            logger.info(f"[连接 {self.connection_id}] 测试数据已保存: {args}")

    def get_input_data(self) -> dict:
        """获取存储的测试数据"""
        return {
            "connection_id": self.connection_id,
            "input_data": self.input_data,
            "mode": str(self.mode),
            "video_resolution": self.video_resolution,
        }

    def copy(self) -> "UranEchoHandler":
        return UranEchoHandler(
            expected_layout=self.expected_layout,
            output_sample_rate=self.output_sample_rate,
            output_frame_size=self.output_frame_size,
        )

    # ========================================================================
    # 视频处理方法
    # ========================================================================

    async def video_receive(self, frame: np.ndarray):
        """接收客户端的视频帧并排队以进行回声。"""
        # frame 是 (Height, Width, Channels)
        self.total_frames_received += 1

        # 记录视频分辨率变化
        height, width = frame.shape[:2]
        new_resolution = (width, height)

        if self.video_resolution != new_resolution:
            if self.video_resolution is None:
                # 首次接收视频帧，打印详细信息用于调试颜色问题
                channels = frame.shape[2] if len(frame.shape) > 2 else 1
                logger.info(
                    f"[连接 {self.connection_id}] 视频流已建立，分辨率: {width}x{height}, "
                    f"通道数: {channels}, dtype: {frame.dtype}, 颜色范围: [{frame.min()}, {frame.max()}]"
                )
            else:
                logger.warning(
                    f"[连接 {self.connection_id}] 视频分辨率已改变: "
                    f"{self.video_resolution[0]}x{self.video_resolution[1]} -> {width}x{height}"
                )
            self.video_resolution = new_resolution

        # 如果抽帧已启用，更新缓存
        if self.frame_capture_enabled:
            self.latest_video_frame = frame.copy()

        # ============ 异步视频录制 ============
        # 如果视频录制已启用，将帧放入队列（非阻塞）
        if self.video_recording_enabled:
            try:
                # 使用 put_nowait 避免阻塞主流程
                self.video_recording_queue.put_nowait(frame.copy())
                self.recorded_video_frames += 1

                # 监控队列大小
                queue_size = self.video_recording_queue.qsize()
                self.stats["video_queue_max_size"] = max(
                    self.stats["video_queue_max_size"], queue_size
                )

                # 队列使用率警告
                from constants import AsyncTaskConstants

                usage_rate = queue_size / AsyncTaskConstants.VIDEO_RECORDING_QUEUE_SIZE
                if usage_rate > AsyncTaskConstants.QUEUE_WARNING_THRESHOLD:
                    logger.warning(
                        f"[连接 {self.connection_id}] 视频录制队列使用率较高: {usage_rate:.1%}"
                    )
            except asyncio.QueueFull:
                # 队列满了，丢弃帧并记录
                self.stats["video_dropped_frames"] += 1
                from constants import AsyncTaskConstants

                if (
                    self.stats["video_dropped_frames"]
                    % AsyncTaskConstants.DROPPED_FRAME_LOG_INTERVAL
                    == 0
                ):
                    logger.warning(
                        f"[连接 {self.connection_id}] 视频录制队列已满，"
                        f"已丢弃 {self.stats['video_dropped_frames']} 帧"
                    )

        await self.video_queue.put(frame)

    async def video_emit(self) -> VideoEmitType:
        """向客户端发送视频帧。"""
        return await self.video_queue.get()

    # ========================================================================
    # 音频处理方法
    # ========================================================================

    async def receive(self, frame: Tuple[int, np.ndarray]) -> None:
        """接收客户端的音频帧。"""
        sample_rate, audio_data = frame
        self.sample_rate = sample_rate  # 如果需要，更新采样率

        # ============ 异步音频录制 ============
        if self.mode == StreamMode.RECORDING:
            try:
                # 将音频帧放入异步录制队列
                self.audio_recording_queue.put_nowait(audio_data.copy())

                # 监控队列
                queue_size = self.audio_recording_queue.qsize()
                self.stats["audio_queue_max_size"] = max(
                    self.stats["audio_queue_max_size"], queue_size
                )
            except asyncio.QueueFull:
                self.stats["audio_dropped_frames"] += 1
                # 音频丢帧比较严重，可以降低日志频率
                if self.stats["audio_dropped_frames"] % 100 == 0:
                    logger.warning(
                        f"[连接 {self.connection_id}] 音频录制队列已满，丢弃帧"
                    )

            # 兼容旧逻辑：同时也存入内存列表（为了回放功能）
            self.recorded_audio_frames.append(audio_data.copy())

        # 始终排队进行实时回声
        await self.audio_queue.put(frame)

    async def emit(self) -> AudioEmitType:
        """向客户端发送音频。"""
        if self.mode == StreamMode.REPLAYING:
            # 回放逻辑
            if self.replay_index < len(self.recorded_audio_frames):
                audio_data = self.recorded_audio_frames[self.replay_index]
                self.replay_index += 1

                # 排空实时队列以防止堆积，但不发送它
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                return (self.sample_rate, audio_data)
            else:
                # 回放结束
                logger.info(f"回放结束，切换回 {StreamMode.LIVE.description} 模式")
                self.mode = StreamMode.LIVE
                self.replay_index = 0
                if self.channel:
                    self.channel.send(
                        json.dumps(
                            {"type": MessageType.STATUS.value, "message": "回放结束"}
                        )
                    )

        # LIVE 或 RECORDING 模式：回声实时音频
        return await wait_for_item(self.audio_queue)

    # ========================================================================
    # DataChannel 消息处理
    # ========================================================================

    def text_receive(self, message: str):
        """处理 DataChannel 消息。"""
        logger.info(f"收到消息: {message}")
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == MessageType.START_RECORD.value:
                self.start_audio_recording()
            elif action == MessageType.STOP_RECORD.value:
                self.stop_audio_recording()
            elif action == MessageType.START_FRAME_CAPTURE.value:
                self.start_frame_capture()
            elif action == MessageType.STOP_FRAME_CAPTURE.value:
                self.stop_frame_capture()
            elif action == MessageType.START_VIDEO_RECORDING.value:
                self.start_video_recording()
            elif action == MessageType.STOP_VIDEO_RECORDING.value:
                self.stop_video_recording()

        except json.JSONDecodeError:
            logger.error("解码 JSON 消息失败")

    # ========================================================================
    # 音频录制功能
    # ========================================================================

    def start_audio_recording(self):
        logger.info(f"[连接 {self.connection_id}] 开始音频录制")
        self.mode = StreamMode.RECORDING
        self.recorded_audio_frames = []  # 仍保留用于回放，但录制文件由worker处理

        # 生成文件名
        timestamp = int(time.time())
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(record_audio_dir_path, filename)

        # 启动异步worker任务
        from handlers.async_workers import AudioRecordingWorker

        self.audio_recording_worker_task = asyncio.create_task(
            AudioRecordingWorker.run(
                queue=self.audio_recording_queue,
                connection_id=self.connection_id,
                sample_rate=self.sample_rate,
                filepath=filepath,
            )
        )

        if self.channel:
            self.channel.send(
                json.dumps({"type": MessageType.STATUS.value, "message": "录制已开始"})
            )

    async def _stop_audio_recording_async(self):
        """异步停止音频录制"""
        if self.mode != StreamMode.RECORDING:
            return

        try:
            # 1. 切换状态停止接收
            self.mode = StreamMode.REPLAYING
            self.replay_index = 0

            # 2. 等待队列清空
            from constants import AsyncTaskConstants

            start_time = time.time()
            while not self.audio_recording_queue.empty():
                if time.time() - start_time > AsyncTaskConstants.SHUTDOWN_WAIT_TIMEOUT:
                    logger.warning(
                        f"[连接 {self.connection_id}] 等待音频录制队列清空超时"
                    )
                    break
                await asyncio.sleep(0.1)

            # 3. 等待worker完成
            if self.audio_recording_worker_task:
                try:
                    # worker会在队列为空且超时后自动结束，或者我们可以cancel它
                    # 但AudioRecordingWorker设计是读到超时才结束，所以这里可能需要一点时间
                    # 或者我们可以修改worker支持显式停止信号，但目前利用超时机制
                    await asyncio.wait_for(
                        self.audio_recording_worker_task,
                        timeout=AsyncTaskConstants.QUEUE_GET_TIMEOUT + 2.0,
                    )
                except asyncio.TimeoutError:
                    # 如果超时还没结束，强制取消
                    self.audio_recording_worker_task.cancel()
                except Exception as e:
                    logger.error(f"[连接 {self.connection_id}] 音频worker关闭异常: {e}")
                self.audio_recording_worker_task = None

            logger.info(
                f"[连接 {self.connection_id}] 停止音频录制 (内存中保留 {len(self.recorded_audio_frames)} 帧用于回放)"
            )

            if self.channel:
                self.channel.send(
                    json.dumps(
                        {
                            "type": MessageType.STATUS.value,
                            "message": "录制已停止，正在回放...",
                        }
                    )
                )
        except Exception as e:
            logger.error(f"[连接 {self.connection_id}] 停止音频录制时出错: {e}")

    def stop_audio_recording(self):
        logger.info(f"[连接 {self.connection_id}] 收到停止录制请求")
        if self.mode != StreamMode.RECORDING:
            return

        # 启动后台任务停止录制
        asyncio.create_task(self._stop_audio_recording_async())

    # ========================================================================
    # 视频抽帧功能
    # ========================================================================

    def start_frame_capture(self):
        """启动视频抽帧"""
        if self.frame_capture_enabled:
            logger.warning(
                f"[连接 {self.connection_id}] 抽帧已经在运行中，忽略重复请求"
            )
            return

        if self.video_resolution is None:
            logger.warning(f"[连接 {self.connection_id}] 视频流尚未建立，无法启动抽帧")
            if self.channel:
                self.channel.send(
                    json.dumps(
                        {
                            "type": MessageType.FRAME_CAPTURE_STATUS.value,
                            "message": "视频流尚未建立，请稍后重试",
                        }
                    )
                )
            return

        logger.info(
            f"[连接 {self.connection_id}] 启动视频抽帧 (分辨率: {self.video_resolution[0]}x{self.video_resolution[1]}, "
            f"间隔: {VideoConstants.FRAME_CAPTURE_INTERVAL}秒)"
        )
        self.frame_capture_enabled = True
        self.frame_count = 0

        timestamp = int(time.time())
        filename = f"frame_{timestamp}.png"
        filepath = os.path.join(video_frames_dir_path, filename)

        # 启动异步worker任务（消费者）
        from handlers.async_workers import FrameSaveWorker

        self.frame_save_worker_task = asyncio.create_task(
            FrameSaveWorker.run(
                queue=self.frame_save_queue,
                connection_id=self.connection_id,
                get_enabled_func=lambda: self.frame_capture_enabled,
                get_count_func=lambda: self.frame_count,
                increment_count_func=lambda: setattr(
                    self, "frame_count", self.frame_count + 1
                ),
                filepath=filepath,
            )
        )

        # 启动抽帧循环任务（生产者）
        self.frame_capture_task = asyncio.create_task(self.frame_capture_loop())

        if self.channel:
            self.channel.send(
                json.dumps(
                    {
                        "type": MessageType.FRAME_CAPTURE_STATUS.value,
                        "message": "抽帧已开始",
                    }
                )
            )

    def stop_frame_capture(self):
        """停止视频抽帧"""
        if not self.frame_capture_enabled:
            logger.warning(f"[连接 {self.connection_id}] 抽帧未在运行，忽略停止请求")
            return

        logger.info(
            f"[连接 {self.connection_id}] 停止视频抽帧 (共保存 {self.frame_count} 帧)"
        )
        self.frame_capture_enabled = False

        # 取消循环任务
        if self.frame_capture_task:
            self.frame_capture_task.cancel()
            self.frame_capture_task = None

        # worker任务会在 frame_capture_enabled 变为 False 后自动退出（处理完队列后）
        # 这里不需要手动取消 worker，除非需要强制立即停止

        if self.channel:
            self.channel.send(
                json.dumps(
                    {
                        "type": MessageType.FRAME_CAPTURE_STATUS.value,
                        "message": f"抽帧已停止，共保存 {self.frame_count} 帧",
                    }
                )
            )

    async def frame_capture_loop(self):
        """抽帧循环任务，每 3 秒将当前帧放入队列"""
        logger.info(f"[连接 {self.connection_id}] 抽帧循环任务已启动")
        try:
            while self.frame_capture_enabled:
                await asyncio.sleep(VideoConstants.FRAME_CAPTURE_INTERVAL)

                if self.latest_video_frame is not None:
                    try:
                        # 将帧放入队列
                        self.frame_save_queue.put_nowait(self.latest_video_frame.copy())
                    except asyncio.QueueFull:
                        self.stats["frame_save_dropped"] += 1
                        logger.warning(
                            f"[连接 {self.connection_id}] 抽帧队列已满，丢弃本次抽帧"
                        )
                else:
                    logger.warning(
                        f"[连接 {self.connection_id}] 没有可用的视频帧，跳过本次抽帧"
                    )
        except asyncio.CancelledError:
            logger.info(f"[连接 {self.connection_id}] 抽帧循环任务已取消")
        except Exception as e:
            logger.error(f"[连接 {self.connection_id}] 抽帧循环任务异常: {e}")

    # ========================================================================
    # 视频录制功能
    # ========================================================================

    def start_video_recording(self):
        """启动视频流录制"""
        if self.video_recording_enabled:
            logger.warning(
                f"[连接 {self.connection_id}] 视频录制已经在进行中，忽略重复请求"
            )
            return

        if self.video_resolution is None:
            logger.warning(
                f"[连接 {self.connection_id}] 视频流尚未建立，无法启动视频录制"
            )
            if self.channel:
                self.channel.send(
                    json.dumps(
                        {
                            "type": MessageType.VIDEO_RECORDING_STATUS.value,
                            "message": "视频流尚未建立，请稍后重试",
                        }
                    )
                )
            return

        try:
            # 生成带时间戳的视频文件名
            timestamp = int(time.time())
            filename = f"video_{timestamp}.avi"
            self.video_recording_path = os.path.join(
                video_recordings_dir_path, filename
            )

            # 创建 VideoWriter
            # 使用 XVID 编码器保存为 AVI，通常兼容性和颜色表现更好
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            fps = VideoConstants.DEFAULT_FPS  # 帧率
            width, height = self.video_resolution

            self.video_writer = cv2.VideoWriter(
                self.video_recording_path, fourcc, fps, (width, height)
            )

            if not self.video_writer.isOpened():
                raise Exception("无法创建视频写入器")

            self.video_recording_enabled = True
            self.recorded_video_frames = 0

            # ✨ 启动异步worker任务
            from handlers.async_workers import VideoRecordingWorker

            self.video_recording_worker_task = asyncio.create_task(
                VideoRecordingWorker.run(
                    queue=self.video_recording_queue,
                    video_writer=self.video_writer,
                    connection_id=self.connection_id,
                    stats=self.stats,
                    get_enabled_func=lambda: self.video_recording_enabled,
                    resolution=(width, height),
                )
            )
            logger.info(f"[连接 {self.connection_id}] 视频录制worker任务已启动")

            logger.info(
                f"[连接 {self.connection_id}] 启动视频录制: {filename} "
                f"(分辨率: {width}x{height}, 帧率: {fps} fps)"
            )

            if self.channel:
                self.channel.send(
                    json.dumps(
                        {
                            "type": MessageType.VIDEO_RECORDING_STATUS.value,
                            "message": "视频录制已开始",
                        }
                    )
                )
        except Exception as e:
            logger.error(f"[连接 {self.connection_id}] 启动视频录制失败: {e}")
            if self.channel:
                self.channel.send(
                    json.dumps(
                        {
                            "type": MessageType.VIDEO_RECORDING_STATUS.value,
                            "message": f"启动视频录制失败: {e}",
                        }
                    )
                )

    async def _stop_video_recording_async(self):
        """异步停止视频录制"""
        if not self.video_recording_enabled:
            return

        try:
            # 1. 停止接收新帧
            self.video_recording_enabled = False

            # 2. 等待worker处理完队列中的帧（带超时）
            from constants import AsyncTaskConstants

            start_time = time.time()
            while not self.video_recording_queue.empty():
                if time.time() - start_time > AsyncTaskConstants.SHUTDOWN_WAIT_TIMEOUT:
                    logger.warning(
                        f"[连接 {self.connection_id}] 等待视频录制队列清空超时"
                    )
                    break
                await asyncio.sleep(0.1)

            # 3. 等待worker任务完成
            if self.video_recording_worker_task:
                try:
                    await asyncio.wait_for(
                        self.video_recording_worker_task, timeout=2.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"[连接 {self.connection_id}] 视频录制worker关闭超时"
                    )
                    self.video_recording_worker_task.cancel()
                except Exception as e:
                    logger.error(
                        f"[连接 {self.connection_id}] 视频录制worker关闭异常: {e}"
                    )
                self.video_recording_worker_task = None

            # 4. 释放资源
            if self.video_writer is not None:
                # 在线程中释放，避免阻塞
                await asyncio.to_thread(self.video_writer.release)
                self.video_writer = None

            logger.info(
                f"[连接 {self.connection_id}] 停止视频录制: {self.video_recording_path} "
                f"(共录制 {self.recorded_video_frames} 帧)"
            )

            if self.channel:
                self.channel.send(
                    json.dumps(
                        {
                            "type": MessageType.VIDEO_RECORDING_STATUS.value,
                            "message": f"视频录制已停止，共录制 {self.recorded_video_frames} 帧",
                            "filename": (
                                os.path.basename(self.video_recording_path)
                                if self.video_recording_path
                                else None
                            ),
                            "path": self.video_recording_path,
                        }
                    )
                )
        except Exception as e:
            logger.error(f"[连接 {self.connection_id}] 停止视频录制时出错: {e}")

    def stop_video_recording(self):
        """停止视频流录制（同步入口，实际调用异步方法）"""
        if not self.video_recording_enabled:
            logger.warning(
                f"[连接 {self.connection_id}] 视频录制未在进行，忽略停止请求"
            )
            return

        # 创建后台任务来执行停止逻辑
        asyncio.create_task(self._stop_video_recording_async())
