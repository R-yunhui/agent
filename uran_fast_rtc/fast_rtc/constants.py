"""
FastRTC 常量定义模块

包含应用程序中使用的所有枚举类型和常量定义
"""
from enum import Enum, auto


class StreamMode(str, Enum):
    """音频流处理模式
    
    定义音频流的三种处理状态：
    - LIVE: 实时直播模式，音频直接回传
    - RECORDING: 录制模式，保存音频数据
    - REPLAYING: 回放模式，播放已录制的音频
    """
    LIVE = "LIVE"
    RECORDING = "RECORDING"
    REPLAYING = "REPLAYING"
    
    def __str__(self) -> str:
        """返回枚举值的字符串表示"""
        return self.value
    
    @property
    def description(self) -> str:
        """返回模式的中文描述"""
        descriptions = {
            StreamMode.LIVE: "直播",
            StreamMode.RECORDING: "录制", 
            StreamMode.REPLAYING: "回放"
        }
        return descriptions.get(self, "未知")


class MessageType(str, Enum):
    """DataChannel 消息类型
    
    定义前后端通信的消息类型
    """
    # 控制消息
    START_RECORD = "start_record"
    STOP_RECORD = "stop_record"
    START_FRAME_CAPTURE = "start_frame_capture"
    STOP_FRAME_CAPTURE = "stop_frame_capture"
    START_VIDEO_RECORDING = "start_video_recording"
    STOP_VIDEO_RECORDING = "stop_video_recording"
    
    # 状态消息
    STATUS = "status"
    SAVED = "saved"
    FRAME_CAPTURE_STATUS = "frame_capture_status"
    FRAME_SAVED = "frame_saved"
    VIDEO_RECORDING_STATUS = "video_recording_status"


class VideoCodec(str, Enum):
    """视频编码器类型"""
    MP4V = "mp4v"
    H264 = "h264"
    XVID = "XVID"


# 视频录制相关常量
class VideoConstants:
    """视频录制相关常量"""
    DEFAULT_FPS = 30  # 默认帧率
    DEFAULT_BITRATE = 2500000  # 默认码率 2.5 Mbps
    FRAME_CAPTURE_INTERVAL = 3  # 抽帧间隔（秒）
    MAX_FILE_LIST_SIZE = 20  # 文件列表最大显示数量


# 音频录制相关常量
class AudioConstants:
    """音频录制相关常量"""
    DEFAULT_SAMPLE_RATE = 24000  # 默认采样率
    DEFAULT_FRAME_SIZE = 480  # 默认帧大小
    INPUT_SAMPLE_RATE = 16000  # 输入采样率


# 目录路径常量
class PathConstants:
    """文件路径常量"""
    RECORD_AUDIO_DIR = "record_audio"
    VIDEO_FRAMES_DIR = "video_frames"
    VIDEO_RECORDINGS_DIR = "video_recordings"
