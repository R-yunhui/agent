"""
FastRTC Demo - 双向音频（不需要 VAD）
接收音频 -> 保存文件 -> 回传音频
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastrtc import Stream, StreamHandler
import numpy as np
from pathlib import Path
import uvicorn
import soundfile as sf
from queue import Queue
from datetime import datetime

# 创建 FastAPI 应用
app = FastAPI(title="FastRTC Echo Demo")

# 全局变量存储最新的 handler 实例
latest_handler: "EchoHandler" = None

class EchoHandler(StreamHandler):
    """
    音频回声处理器（不需要 VAD）
    接收音频 -> 缓存 -> 等待指令 -> 保存文件 -> 回传音频
    """
    
    def __init__(self):
        self.audio_queue = Queue()  # 用于回传的音频队列
        self.buffer = [] # 用于录制的音频缓存
        self.recording = True # 是否正在录制
        self.sample_rate = 48000 # 默认采样率
        self.output_dir = Path(__file__).parent / "recordings"
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置全局 handler，以便 API 可以访问
        global latest_handler
        latest_handler = self
    
    def copy(self):
        """返回当前 handler 的副本"""
        return EchoHandler()
    
    def receive(self, audio: tuple[int, np.ndarray]):
        """
        接收来自客户端的音频
        
        参数:
            audio: (采样率, 音频数据)
        """
        sample_rate, audio_data = audio
        
        self.sample_rate = sample_rate
        
        if self.recording:
            # 录制阶段：只缓存，不回传
            self.buffer.append(audio_data)
            print(f"📥 接收音频: {len(audio_data)} samples (缓存中...)")
        else:
            # 非录制阶段：直接丢弃或做其他处理
            pass

    def save_and_replay(self):
        """保存缓存的音频并准备回传"""
        self.recording = False
        
        if not self.buffer:
            print("⚠️ 没有录制到音频")
            return {"status": "no_audio"}

        # 合并音频数据
        full_audio = np.concatenate(self.buffer)
        self.buffer = [] # 清空缓存
        
        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"audio_{timestamp}.wav"
        
        try:
            sf.write(str(filename), full_audio, self.sample_rate)
            print(f"💾 已保存录音: {filename}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return {"status": "error", "message": str(e)}
            
        # 将音频切片放入队列，准备回传
        # 模拟流式回传，将大文件切成小块
        chunk_size = 4800 # 100ms at 48kHz
        for i in range(0, len(full_audio), chunk_size):
            chunk = full_audio[i:i+chunk_size]
            self.audio_queue.put((self.sample_rate, chunk))
            
        print(f"🔄 已加入回放队列: {len(full_audio)} samples")
        return {"status": "ok", "file": str(filename)}
    
    def emit(self) -> tuple[int, np.ndarray]:
        """
        发送音频给客户端（回声效果）
        
        返回:
            音频数据 (采样率, 音频数组)
        """
        # 如果队列中有音频，就返回
        if not self.audio_queue.empty():
            audio = self.audio_queue.get()
            sample_rate, audio_data = audio
            # print(f"📤 回放音频: {len(audio_data)} samples")
            return audio
        
        # 否则返回静音
        sample_rate = 48000
        silence = np.zeros(4800, dtype=np.int16)  # 100ms 静音
        return (sample_rate, silence)


# 创建 Stream
stream = Stream(
    handler=EchoHandler(),
    modality="audio",
    mode="send-receive",  # 双向模式
)

# 挂载到 FastAPI
stream.mount(app)


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回前端页面"""
    html_file = Path(__file__).parent / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>❌ index.html 未找到</h1>")


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "mode": "send-receive",
        "features": ["audio-recording", "audio-replay"]
    }

@app.post("/replay")
async def replay():
    """触发回放"""
    if latest_handler:
        return latest_handler.save_and_replay()
    return {"status": "error", "message": "No active handler"}


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 FastRTC 双向音频 Demo (无 VAD)")
    print("=" * 60)
    print("📍 访问: http://localhost:8000")
    print("💡 功能:")
    print("   - 接收麦克风音频")
    print("   - 保存为 WAV 文件")
    print("   - 回传音频（回声效果）")
    print(f"📁 音频保存位置: {Path(__file__).parent / 'recordings'}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
