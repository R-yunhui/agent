import asyncio
import json
import logging
import os
# import requests # 保留，但在此次回声功能中未使用
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
# from aiortc.contrib.media import MediaBlackhole # 不再需要
# from aiortc.contrib.media import MediaRecorder # 在此功能中不使用

# 设置日志
logging.basicConfig(level=logging.INFO)
ROOT = os.path.dirname(__file__)

pcs = set()


async def index(request):
    """提供前端 HTML 页面"""
    content = open(os.path.join(ROOT, "web/index.html"), "r", encoding="utf-8").read()
    return web.Response(content_type="text/html", text=content)


async def offer(request):
    """处理来自前端的 WebRTC Offer"""
    params = await request.json()
    offer_info = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logging.info(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        logging.info(f"Track {track.kind} received. Echoing it back to the client.")
        # 关键改动：将接收到的轨道添加回连接中，实现回声
        pc.addTrack(track)

        # --- 以下是您之前添加的代码，暂时注释掉 ---
        # recorder = MediaBlackhole()
        # recorder.addTrack(track)
        # from aiortc.contrib.media import MediaRecorder
        # recorder = MediaRecorder("received_audio.wav")
        # recorder.addTrack(track)
        # asyncio.ensure_future(recorder.start())
        #
        # # 调用 讯飞 tts 接口，语音转文本
        # --- 注释结束 ---

    # 设置远端描述
    await pc.setRemoteDescription(offer_info)

    # 创建并返回 Answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app):
    """关闭所有 RTCPeerConnection"""
    # 关闭所有活动的连接
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_post("/offer", offer)

    # 添加静态文件路由
    app.router.add_static('/web/', path=os.path.join(ROOT, 'web'), name='web')

    web.run_app(app, host="0.0.0.0", port=8080)
