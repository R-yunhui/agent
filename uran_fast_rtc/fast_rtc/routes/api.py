"""
API 路由模块

负责 WebRTC 连接管理相关的 API 路由定义。
这是非业务逻辑代码，专注于 HTTP API 层。
"""
import time
import logging
from fastapi import APIRouter, HTTPException
from fastrtc import Stream

logger = logging.getLogger("uran_fast_rtc")


def create_api_router(stream: Stream) -> APIRouter:
    """
    创建 API 路由器
    
    Args:
        stream: FastRTC Stream 实例，用于访问连接信息
    
    Returns:
        配置好的 APIRouter 实例
    """
    router = APIRouter(prefix="/api")
    
    @router.get("/connections")
    async def list_connections():
        """获取所有活跃连接信息"""
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
    
    @router.post("/connections/{webrtc_id}/input-data")
    async def set_input_data(webrtc_id: str, data: dict):
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
    
    @router.get("/connections/{webrtc_id}/input-data")
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
            
            # conn_list 里面包含了两个连接，一个视频流的连接通道，一个音频流的连接通道
            conn = conn_list[0]
            event_handler = getattr(conn, 'event_handler', None)
            
            if not event_handler:
                raise HTTPException(500, "无法获取 event_handler")
            
            # 调用 handler 的 get_input_data 方法
            input_data = event_handler.get_input_data()
            
            return {
                "status": "success",
                "webrtc_id": webrtc_id,
                "data": input_data
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取测试数据时出错: {e}")
            raise HTTPException(500, str(e))
    
    return router
