import asyncio
import json
import logging
import os
import time
from typing import Tuple, List, Optional, Union
import numpy as np
import soundfile as sf
import cv2
from PIL import Image
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastrtc import (
    AsyncAudioVideoStreamHandler,
    Stream,
    get_twilio_turn_credentials,
    AudioEmitType,
    VideoEmitType,
    wait_for_item
)
from aiortc import RTCDataChannel

# 导入常量定义
from constants import (
    StreamMode,
    MessageType,
    VideoCodec,
    VideoConstants,
    AudioConstants,
    PathConstants
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uran_fast_rtc")

class UranEchoHandler(AsyncAudioVideoStreamHandler):
    def __init__(
        self, expected_layout="mono", output_sample_rate=24000, output_frame_size=480
    ) -> None:
        super().__init__(
            expected_layout,
            output_sample_rate,
            output_frame_size,
            input_sample_rate=16000,
        )
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
        
        # 测试数据存储（用于 set_input 测试）
        self.test_data = {}  # 存储通过 set_input 传递的测试数据

    async def start_up(self):
        """连接建立时调用。"""
        import time
        self.connection_id = id(self)
        self.start_time = time.time()
        
        logger.info(f"[连接 {self.connection_id}] WebRTC 连接已建立")
        logger.info(f"[连接 {self.connection_id}] 连接时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}")
        
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
            self.stop_video_recording()
        
        # 记录统计信息
        logger.info(
            f"[连接 {self.connection_id}] 统计：总接收视频帧 {self.total_frames_received} 帧，"
            f"抽帧保存 {self.frame_count} 帧，视频录制 {self.recorded_video_frames} 帧"
        )
        logger.info(f"[连接 {self.connection_id}] 连接已关闭")
    
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
            self.test_data.update(args[0])
            logger.info(f"[连接 {self.connection_id}] 测试数据已更新: {self.test_data}")
        
        # 情况 2: 传递的是字符串或其他类型
        else:
            self.test_data["last_input"] = args
            logger.info(f"[连接 {self.connection_id}] 测试数据已保存: {args}")
    
    def get_input_data(self) -> dict:
        """获取存储的测试数据"""
        return {
            "connection_id": self.connection_id,
            "input_data": self.test_data,
            "mode": str(self.mode),
            "video_resolution": self.video_resolution
        }

    def copy(self) -> "UranEchoHandler":
        return UranEchoHandler(
            expected_layout=self.expected_layout,
            output_sample_rate=self.output_sample_rate,
            output_frame_size=self.output_frame_size,
        )

    async def video_receive(self, frame: np.ndarray):
        """接收客户端的视频帧并排队以进行回声。"""
        # frame 是 (Height, Width, Channels)
        self.total_frames_received += 1
        
        # 记录视频分辨率变化
        height, width = frame.shape[:2]
        new_resolution = (width, height)
        
        if self.video_resolution != new_resolution:
            if self.video_resolution is None:
                logger.info(f"[连接 {self.connection_id}] 视频流已建立，分辨率: {width}x{height}")
            else:
                logger.warning(
                    f"[连接 {self.connection_id}] 视频分辨率已改变: "
                    f"{self.video_resolution[0]}x{self.video_resolution[1]} -> {width}x{height}"
                )
            self.video_resolution = new_resolution
        
        # 如果抽帧已启用，更新缓存
        if self.frame_capture_enabled:
            self.latest_video_frame = frame.copy()
        
        # 如果视频录制已启用，写入视频文件
        if self.video_recording_enabled and self.video_writer is not None:
            try:
                # OpenCV 需要 BGR 格式，frame 可能是 RGB
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) if frame.shape[2] == 3 else frame
                self.video_writer.write(bgr_frame)
                self.recorded_video_frames += 1
            except Exception as e:
                logger.error(f"[连接 {self.connection_id}] 写入视频帧失败: {e}")
        
        await self.video_queue.put(frame)

    async def video_emit(self) -> VideoEmitType:
        """向客户端发送视频帧。"""
        return await self.video_queue.get()

    async def receive(self, frame: Tuple[int, np.ndarray]) -> None:
        """接收客户端的音频帧。"""
        sample_rate, audio_data = frame
        self.sample_rate = sample_rate # 如果需要，更新采样率

        if self.mode == StreamMode.RECORDING:
            # 存储数据副本以进行录制
            self.recorded_audio_frames.append(audio_data.copy())
        
        # 始终排队进行实时回声（除非我们想在回放期间静音，在 emit 中处理）
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
                    self.channel.send(json.dumps({"type": MessageType.STATUS.value, "message": "回放结束"}))

        # LIVE 或 RECORDING 模式：回声实时音频
        return await wait_for_item(self.audio_queue)

    def text_receive(self, message: str):
        """处理 DataChannel 消息。"""
        logger.info(f"收到消息: {message}")
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == MessageType.START_RECORD.value:
                self.start_recording()
            elif action == MessageType.STOP_RECORD.value:
                self.stop_recording()
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

    def start_recording(self):
        logger.info(f"[连接 {self.connection_id}] 开始音频录制")
        self.mode = StreamMode.RECORDING
        self.recorded_audio_frames = []
        if self.channel:
            self.channel.send(json.dumps({"type": MessageType.STATUS.value, "message": "录制已开始"}))

    def stop_recording(self):
        logger.info(f"[连接 {self.connection_id}] 停止音频录制 (共录制 {len(self.recorded_audio_frames)} 帧)")
        self.mode = StreamMode.REPLAYING  # 停止后直接切换到回放
        self.replay_index = 0
        
        # 保存到文件
        self.save_recording()
        
        if self.channel:
            self.channel.send(json.dumps({"type": MessageType.STATUS.value, "message": "录制已停止，正在保存并回放..."}))

    def save_recording(self):
        if not self.recorded_audio_frames:
            logger.warning("没有音频帧可保存。")
            return

        try:
            # 连接所有帧
            full_audio = np.concatenate(self.recorded_audio_frames)
            
            # 生成带时间戳的文件名
            filename = f"recording_{int(time.time())}.wav"
            filepath = os.path.join(record_audio_dir_path, filename)
            
            # 保存为 WAV
            sf.write(filepath, full_audio, self.sample_rate)
            logger.info(f"录音已保存到 {filepath}")
            
            if self.channel:
                self.channel.send(json.dumps({
                    "type": MessageType.SAVED.value, 
                    "filename": filename,
                    "path": filepath
                }))
        except Exception as e:
            logger.error(f"保存录音时出错: {e}")
    
    def start_frame_capture(self):
        """启动视频抽帧"""
        if self.frame_capture_enabled:
            logger.warning(f"[连接 {self.connection_id}] 抽帧已经在运行中，忽略重复请求")
            return
        
        if self.video_resolution is None:
            logger.warning(f"[连接 {self.connection_id}] 视频流尚未建立，无法启动抽帧")
            if self.channel:
                self.channel.send(json.dumps({
                    "type": MessageType.FRAME_CAPTURE_STATUS.value,
                    "message": "视频流尚未建立，请稍后重试"
                }))
            return
        
        logger.info(
            f"[连接 {self.connection_id}] 启动视频抽帧 (分辨率: {self.video_resolution[0]}x{self.video_resolution[1]}, "
            f"间隔: {VideoConstants.FRAME_CAPTURE_INTERVAL}秒)"
        )
        self.frame_capture_enabled = True
        self.frame_count = 0
        
        # 创建 asyncio 任务
        self.frame_capture_task = asyncio.create_task(self.frame_capture_loop())
        
        if self.channel:
            self.channel.send(json.dumps({
                "type": MessageType.FRAME_CAPTURE_STATUS.value,
                "message": "抽帧已开始"
            }))
    
    def stop_frame_capture(self):
        """停止视频抽帧"""
        if not self.frame_capture_enabled:
            logger.warning(f"[连接 {self.connection_id}] 抽帧未在运行，忽略停止请求")
            return
        
        logger.info(f"[连接 {self.connection_id}] 停止视频抽帧 (共保存 {self.frame_count} 帧)")
        self.frame_capture_enabled = False
        
        # 取消 asyncio 任务
        if self.frame_capture_task:
            self.frame_capture_task.cancel()
            self.frame_capture_task = None
        
        if self.channel:
            self.channel.send(json.dumps({
                "type": MessageType.FRAME_CAPTURE_STATUS.value,
                "message": f"抽帧已停止，共保存 {self.frame_count} 帧"
            }))
    
    async def frame_capture_loop(self):
        """抽帧循环任务，每 3 秒保存一帧"""
        logger.info(f"[连接 {self.connection_id}] 抽帧循环任务已启动")
        try:
            while self.frame_capture_enabled:
                await asyncio.sleep(VideoConstants.FRAME_CAPTURE_INTERVAL)
                
                if self.latest_video_frame is not None:
                    self.save_video_frame()
                else:
                    logger.warning(f"[连接 {self.connection_id}] 没有可用的视频帧，跳过本次抽帧")
        except asyncio.CancelledError:
            logger.info(f"[连接 {self.connection_id}] 抽帧循环任务已取消")
        except Exception as e:
            logger.error(f"[连接 {self.connection_id}] 抽帧循环任务异常: {e}")
    
    def save_video_frame(self):
        """保存当前视频帧为图片"""
        if self.latest_video_frame is None:
            return
        
        try:
            # 转换 BGR 到 RGB (如果需要)
            frame = self.latest_video_frame
            if frame.shape[2] == 3:  # BGR
                frame = frame[:, :, ::-1]  # BGR to RGB
            
            # 创建 PIL Image
            image = Image.fromarray(frame.astype('uint8'))
            
            # 生成文件名
            timestamp = int(time.time())
            filename = f"frame_{timestamp}_{self.frame_count:04d}.png"
            filepath = os.path.join(video_frames_dir_path, filename)
            
            # 保存图片
            image.save(filepath)
            self.frame_count += 1
            
            logger.info(
                f"[连接 {self.connection_id}] 视频帧已保存: {filename} "
                f"(第 {self.frame_count} 帧, 分辨率: {self.video_resolution[0]}x{self.video_resolution[1]})"
            )
            
            # 发送保存成功消息
            if self.channel:
                self.channel.send(json.dumps({
                    "type": MessageType.FRAME_SAVED.value,
                    "filename": filename,
                    "count": self.frame_count,
                    "resolution": f"{self.video_resolution[0]}x{self.video_resolution[1]}"
                }))
        except Exception as e:
            logger.error(f"[连接 {self.connection_id}] 保存视频帧时出错: {e}")
    
    def start_video_recording(self):
        """启动视频流录制"""
        if self.video_recording_enabled:
            logger.warning(f"[连接 {self.connection_id}] 视频录制已经在进行中，忽略重复请求")
            return
        
        if self.video_resolution is None:
            logger.warning(f"[连接 {self.connection_id}] 视频流尚未建立，无法启动视频录制")
            if self.channel:
                self.channel.send(json.dumps({
                    "type": MessageType.VIDEO_RECORDING_STATUS.value,
                    "message": "视频流尚未建立，请稍后重试"
                }))
            return
        
        try:
            # 生成带时间戳的视频文件名
            timestamp = int(time.time())
            filename = f"video_{timestamp}.mp4"
            self.video_recording_path = os.path.join(video_recordings_dir_path, filename)
            
            # 创建 VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*VideoCodec.MP4V.value)  # MP4 编码器
            fps = VideoConstants.DEFAULT_FPS  # 帧率
            width, height = self.video_resolution
            
            self.video_writer = cv2.VideoWriter(
                self.video_recording_path,
                fourcc,
                fps,
                (width, height)
            )
            
            if not self.video_writer.isOpened():
                raise Exception("无法创建视频写入器")
            
            self.video_recording_enabled = True
            self.recorded_video_frames = 0
            
            logger.info(
                f"[连接 {self.connection_id}] 启动视频录制: {filename} "
                f"(分辨率: {width}x{height}, 帧率: {fps} fps)"
            )
            
            if self.channel:
                self.channel.send(json.dumps({
                    "type": MessageType.VIDEO_RECORDING_STATUS.value,
                    "message": "视频录制已开始"
                }))
        except Exception as e:
            logger.error(f"[连接 {self.connection_id}] 启动视频录制失败: {e}")
            if self.channel:
                self.channel.send(json.dumps({
                    "type": MessageType.VIDEO_RECORDING_STATUS.value,
                    "message": f"启动视频录制失败: {e}"
                }))
    
    def stop_video_recording(self):
        """停止视频流录制"""
        if not self.video_recording_enabled:
            logger.warning(f"[连接 {self.connection_id}] 视频录制未在进行，忽略停止请求")
            return
        
        try:
            self.video_recording_enabled = False
            
            if self.video_writer is not None:
                self.video_writer.release()
                self.video_writer = None
            
            logger.info(
                f"[连接 {self.connection_id}] 停止视频录制: {self.video_recording_path} "
                f"(共录制 {self.recorded_video_frames} 帧)"
            )
            
            if self.channel:
                self.channel.send(json.dumps({
                    "type": MessageType.VIDEO_RECORDING_STATUS.value,
                    "message": f"视频录制已停止，共录制 {self.recorded_video_frames} 帧",
                    "filename": os.path.basename(self.video_recording_path) if self.video_recording_path else None,
                    "path": self.video_recording_path
                }))
        except Exception as e:
            logger.error(f"[连接 {self.connection_id}] 停止视频录制时出错: {e}")

# ============================================================================
# 应用配置类
# ============================================================================
class AppConfig:
    """应用配置管理类"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(__file__)
        self.web_dir = os.path.dirname(self.base_dir)
        
        # HTML 路径
        self.html_path = os.path.join(self.web_dir, "web", "index.html")
        
        # 数据存储路径
        self.record_audio_dir = os.path.join(self.base_dir, PathConstants.RECORD_AUDIO_DIR)
        self.video_frames_dir = os.path.join(self.base_dir, PathConstants.VIDEO_FRAMES_DIR)
        self.video_recordings_dir = os.path.join(self.base_dir, PathConstants.VIDEO_RECORDINGS_DIR)
    
    def init_directories(self):
        """初始化所有必要的目录"""
        directories = [
            self.record_audio_dir,
            self.video_frames_dir,
            self.video_recordings_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"初始化目录: {directory}")


# ============================================================================
# 全局配置实例
# ============================================================================
config = AppConfig()
config.init_directories()

# 为了向后兼容，保留旧的全局变量名
html_path = config.html_path
record_audio_dir_path = config.record_audio_dir
video_frames_dir_path = config.video_frames_dir
video_recordings_dir_path = config.video_recordings_dir


# ============================================================================
# FastAPI 应用初始化
# ============================================================================
def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(
        title="Uran FastRTC Server",
        description="WebRTC 音视频录制服务",
        version="1.0.0"
    )
    
    # 初始化 Stream
    stream = Stream(
        handler=UranEchoHandler(),
        modality="audio-video",
        mode="send-receive",
    )
    
    # 挂载 WebRTC 路由
    stream.mount(app, "/uran-fast-rtc/api")
    
    
    # 前端页面路由
    @app.get("/uran-fast-rtc/test")
    async def serve_frontend():
        """提供前端 HTML 页面"""
        if os.path.exists(config.html_path):
            with open(config.html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        return HTMLResponse(
            content="<h1>未找到前端页面</h1>",
            status_code=404
        )
        
    
    @app.get("/api/connections")
    async def list_connections():
        """获取所有活跃连接信息"""
        import time
        
        connections_list = []
        
        # 遍历所有连接
        for webrtc_id, conn_list in stream.connections.items():
            for conn in conn_list:
                # 获取 handler 实例
                event_handler = getattr(conn, 'event_handler', None)
                if event_handler:
                    connections_list.append({
                        "webrtc_id": webrtc_id,
                        "connection_id": getattr(event_handler, 'connection_id', None),
                        "start_time": getattr(event_handler, 'start_time', None),
                        "connected_duration": int(time.time() - event_handler.start_time) if hasattr(event_handler, 'start_time') and event_handler.start_time else 0,
                        "mode": str(getattr(event_handler, 'mode', 'UNKNOWN')),
                        "video_resolution": getattr(event_handler, 'video_resolution', None),
                        "status": "active"
                    })
        
        return {
            "connections": connections_list,
            "count": len(connections_list)
        }
    
    @app.post("/api/connections/{webrtc_id}/input-data")
    async def set_test_data(webrtc_id: str, data: dict):
        """
        通过 set_input 设置测试数据
        
        示例:
        POST /api/connections/{webrtc_id}/input-data
        {
            "key1": "value1",
            "key2": 123,
            "message": "测试消息"
        }
        """
        if webrtc_id not in stream.connections:
            raise HTTPException(404, f"连接 {webrtc_id} 不存在")
        
        try:
            # 使用 set_input 传递数据
            stream.set_input(webrtc_id, data)
            
            return {
                "status": "success",
                "webrtc_id": webrtc_id,
                "message": "测试数据已设置",
                "data": data
            }
        except Exception as e:
            logger.error(f"设置测试数据时出错: {e}")
            raise HTTPException(500, str(e))
    
    @app.get("/api/connections/{webrtc_id}/input-data")
    async def get_input_data(webrtc_id: str):
        """
        获取连接的测试数据
        
        示例:
        GET /api/connections/{webrtc_id}/input-data
        """
        if webrtc_id not in stream.connections:
            raise HTTPException(404, f"连接 {webrtc_id} 不存在")
        
        try:
            # 获取连接的 handler
            conn_list = stream.connections[webrtc_id]
            if not conn_list:
                raise HTTPException(404, "连接列表为空")
            
            conn = conn_list[0]
            event_handler = getattr(conn, 'event_handler', None)
            
            if not event_handler:
                raise HTTPException(500, "无法获取 event_handler")
            
            # 调用 handler 的 get_input_data 方法
            test_data = event_handler.get_input_data()
            
            return {
                "status": "success",
                "webrtc_id": webrtc_id,
                "data": test_data
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取测试数据时出错: {e}")
            raise HTTPException(500, str(e))
    
    
    @app.get("/")
    async def root():
        """根路径重定向"""
        return {"message": "Uran FastRTC Server", "frontend": "/uran-fast-rtc/test"}
    
    return app


# 创建应用实例
app = create_app()


# ============================================================================
# 主程序入口
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("启动 Uran FastRTC 服务器")
    logger.info(f"前端页面: http://localhost:8000/uran-fast-rtc/test")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
