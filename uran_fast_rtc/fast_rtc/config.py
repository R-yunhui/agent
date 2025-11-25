"""
配置管理模块

负责应用的配置管理，包括路径配置和目录初始化。
这是非业务逻辑代码，专注于配置管理。
"""
import os
import logging
from constants import PathConstants

logger = logging.getLogger("uran_fast_rtc")


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

# 为了向后兼容，提供便捷访问
html_path = config.html_path
record_audio_dir_path = config.record_audio_dir
video_frames_dir_path = config.video_frames_dir
video_recordings_dir_path = config.video_recordings_dir
