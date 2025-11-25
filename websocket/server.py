"""
WebSocket 服务端主程序
支持路径路由和完整的聊天功能，包括房间管理、私聊、广播等
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional, Callable
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
from connection_manager import ConnectionManager
from message_handler import MessageHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# JSON 编码辅助函数，确保中文正常显示
def json_encode(data: dict) -> str:
    """
    JSON 编码，支持中文
    
    Args:
        data: 要编码的字典
    
    Returns:
        JSON 字符串
    """
    return json.dumps(data, ensure_ascii=False)


class WebSocketServer:
    """WebSocket 服务器类 - 支持路径路由"""
    
    def __init__(self, host: str = "localhost", port: int = 8765, default_path: str = "/chat"):
        """
        初始化 WebSocket 服务器
        
        Args:
            host: 服务器监听地址
            port: 服务器监听端口
            default_path: 默认聊天服务路径
        """
        self.host = host
        self.port = port
        self.default_path = default_path
        
        # 聊天服务组件
        self.connection_manager = ConnectionManager()
        self.message_handler = MessageHandler(self.connection_manager)
        
        # 心跳检测配置
        self.ping_interval = 30  # 30秒发送一次心跳
        self.ping_timeout = 10   # 10秒内未响应视为超时
        self.max_ping_retries = 3  # 最大重试次数
        
        # 路由表：路径 -> 处理函数
        self.routes: Dict[str, Callable] = {}
        
        # 统计信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "connections_by_path": {}
        }
        
        # 注册默认路由（完整的聊天服务）
        self.register_route(self.default_path, self.handle_chat_service)
        self.register_route("/", self.handle_chat_service)  # 根路径也指向聊天服务
        
        logger.info(f"聊天服务已注册到路径: {self.default_path} 和 /")
    
    def register_route(self, path: str, handler: Callable):
        """
        注册路由
        
        Args:
            path: 路径
            handler: 处理函数 async def handler(websocket)
        """
        self.routes[path] = handler
        self.stats["connections_by_path"][path] = 0
        logger.info(f"路由已注册: {path}")
    
    def route(self, path: str):
        """
        路由装饰器，方便注册自定义路径
        
        使用方式:
        @server.route("/custom")
        async def handle_custom(websocket):
            ...
        """
        def decorator(handler: Callable):
            self.register_route(path, handler)
            return handler
        return decorator
    
    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """
        处理 WebSocket 连接，根据路径分发到不同的处理器
        
        Args:
            websocket: WebSocket 连接对象
        """
        # 获取请求路径
        path = websocket.request.path
        logger.info(f"收到连接请求，路径: {path}, 来源: {websocket.remote_address}")
        
        # 更新统计
        self.stats["total_connections"] += 1
        self.stats["active_connections"] += 1
        
        try:
            # 查找对应的处理器
            if path in self.routes:
                self.stats["connections_by_path"][path] += 1
                handler = self.routes[path]
                await handler(websocket)
            else:
                # 路径不存在，返回错误
                error_msg = {
                    "type": "error",
                    "message": f"路径 {path} 不存在",
                    "available_paths": list(self.routes.keys())
                }
                await websocket.send(json_encode(error_msg))
                await websocket.close(1008, f"未知路径: {path}")
                logger.warning(f"未知路径: {path}")
        
        except Exception as e:
            logger.error(f"处理连接时发生错误 [{path}]: {e}", exc_info=True)
        
        finally:
            self.stats["active_connections"] -= 1
            logger.info(f"连接已关闭，路径: {path}")
    
    async def handle_chat_service(self, websocket: WebSocketServerProtocol):
        """
        完整的聊天服务处理器（原 handle_client 逻辑）
        支持认证、房间管理、私聊、广播等功能
        
        Args:
            websocket: WebSocket 连接对象
        """
        client_id = None
        try:
            # 等待客户端发送认证信息
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10)
            
            # 尝试解析为 JSON，如果失败则当作普通文本处理
            username = None
            try:
                auth_data = json.loads(auth_message)
                
                # JSON 格式：检查是否为认证消息
                if auth_data.get("type") == "auth":
                    username = auth_data.get("username", f"User_{id(websocket)}")
                else:
                    # JSON 格式但不是认证消息，使用默认用户名
                    logger.warning(f"[聊天服务] 收到非认证 JSON 消息，使用默认用户名")
                    username = f"User_{id(websocket)}"
            
            except json.JSONDecodeError:
                # 普通文本格式：将文本作为用户名
                username = auth_message.strip()
                if not username:
                    username = f"User_{id(websocket)}"
                logger.info(f"[聊天服务] 使用文本格式认证，用户名: {username}")
            
            # 注册客户端
            client_id = await self.connection_manager.register(websocket, username)
            
            logger.info(f"[聊天服务] 客户端已连接: {client_id} (用户名: {username})")
            
            # 发送认证成功消息
            await websocket.send(json_encode({
                "type": "auth_success",
                "client_id": client_id,
                "username": username,
                "message": f"欢迎, {username}!",
                "service": "chat"
            }))
            
            # 启动心跳检测任务
            heartbeat_task = asyncio.create_task(
                self._heartbeat(websocket, client_id)
            )
            
            # 消息处理循环
            async for message in websocket:
                try:
                    # 尝试解析为 JSON
                    try:
                        data = json.loads(message)
                        # JSON 格式：使用消息处理器处理
                        await self.message_handler.handle_message(client_id, data)
                    
                    except json.JSONDecodeError:
                        # 普通文本格式：自动包装成全局聊天消息
                        text_content = message.strip()
                        if text_content:
                            logger.info(f"[聊天服务] 收到文本消息，自动转换为聊天: {text_content}")
                            # 包装成聊天消息格式
                            await self.message_handler.handle_message(client_id, {
                                "type": "chat",
                                "message": text_content
                            })
                        else:
                            logger.warning(f"[聊天服务] 收到空消息")
                
                except Exception as e:
                    logger.error(f"处理消息时发生错误: {e}", exc_info=True)
                    await websocket.send(json_encode({
                        "type": "error",
                        "message": f"处理消息失败: {str(e)}"
                    }))
                    
        except asyncio.TimeoutError:
            logger.warning("[聊天服务] 客户端认证超时")
            await websocket.send(json_encode({
                "type": "error",
                "message": "认证超时"
            }))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"[聊天服务] 客户端连接已关闭: {client_id}")
        except Exception as e:
            logger.error(f"[聊天服务] 处理客户端连接时发生错误: {e}", exc_info=True)
        finally:
            # 取消心跳任务
            if 'heartbeat_task' in locals():
                heartbeat_task.cancel()
            
            # 注销客户端
            if client_id:
                await self.connection_manager.unregister(client_id)
                logger.info(f"[聊天服务] 客户端已断开: {client_id}")
    
    async def _heartbeat(self, websocket: WebSocketServerProtocol, client_id: str):
        """
        心跳检测任务（应用层自定义消息）
        
        工作原理:
        1. 每30秒发送一次自定义心跳消息 {"type": "ping"}
        2. 等待客户端回复 {"type": "pong"}
        3. 失败后重试，最多重试3次
        4. 3次都失败则断开连接
        
        Args:
            websocket: WebSocket 连接对象
            client_id: 客户端ID
        """
        # 用于接收 pong 响应的事件
        pong_received = asyncio.Event()
        ping_id_counter = 0
        current_ping_id = None
        
        # 注册 pong 响应处理器
        async def on_pong(ping_id: int):
            """处理客户端的 pong 响应"""
            nonlocal current_ping_id
            if ping_id == current_ping_id:
                pong_received.set()
        
        # 将 pong 处理器注册到客户端的元数据中
        client = self.connection_manager.get_client(client_id)
        if client:
            client.metadata['pong_handler'] = on_pong
        
        try:
            while True:
                # 等待心跳间隔
                await asyncio.sleep(self.ping_interval)
                
                # 重试逻辑
                retry_count = 0
                success = False
                
                while retry_count < self.max_ping_retries and not success:
                    try:
                        # 准备心跳消息
                        ping_id_counter += 1
                        current_ping_id = ping_id_counter
                        pong_received.clear()
                        
                        # 发送自定义心跳消息
                        ping_message = {
                            "type": "ping",
                            "ping_id": current_ping_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await websocket.send(json_encode(ping_message))
                        logger.debug(f"发送心跳 #{current_ping_id} 给 {client_id} (第 {retry_count + 1} 次尝试)")
                        
                        # 等待 pong 响应（带超时）
                        try:
                            await asyncio.wait_for(
                                pong_received.wait(),
                                timeout=self.ping_timeout
                            )
                            # 收到 pong 响应
                            logger.debug(f"✓ 心跳检测成功: {client_id} (ping_id: {current_ping_id})")
                            success = True
                            
                        except asyncio.TimeoutError:
                            retry_count += 1
                            if retry_count < self.max_ping_retries:
                                logger.warning(
                                    f"⚠ 心跳检测超时: {client_id} "
                                    f"(第 {retry_count}/{self.max_ping_retries} 次失败，将重试)"
                                )
                                # 短暂等待后重试
                                await asyncio.sleep(1)
                            else:
                                logger.error(
                                    f"✗ 心跳检测失败: {client_id} "
                                    f"(重试 {self.max_ping_retries} 次后仍然失败，断开连接)"
                                )
                    
                    except Exception as e:
                        retry_count += 1
                        logger.error(f"发送心跳时发生错误: {e}, 重试 {retry_count}/{self.max_ping_retries}")
                        if retry_count < self.max_ping_retries:
                            await asyncio.sleep(1)
                
                # 所有重试都失败，断开连接
                if not success:
                    logger.warning(f"心跳检测最终失败，断开连接: {client_id}")
                    await websocket.close(1001, "心跳检测失败")
                    break
        
        except asyncio.CancelledError:
            # 任务被取消（正常断开）
            logger.debug(f"心跳任务已取消: {client_id}")
        except Exception as e:
            logger.error(f"心跳检测发生错误: {e}", exc_info=True)
        finally:
            # 清理 pong 处理器
            client = self.connection_manager.get_client(client_id)
            if client and 'pong_handler' in client.metadata:
                del client.metadata['pong_handler']
    
    async def start(self):
        """启动 WebSocket 服务器"""
        logger.info(f"启动 WebSocket 服务器: {self.host}:{self.port}")
        logger.info("已注册的路由:")
        for path in self.routes.keys():
            protocol = "wss" if self.port == 443 else "ws"
            logger.info(f"  - {protocol}://{self.host}:{self.port}{path}")
        
        async with websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=None  # 使用自定义心跳
        ):
            logger.info("WebSocket 服务器已启动，等待连接...")
            await asyncio.Future()  # 永久运行


# ==================== 自定义路由示例 ====================

async def example_notification_handler(websocket: WebSocketServerProtocol):
    """
    示例：通知服务处理器
    可以作为自定义路由的参考
    """
    client_id = id(websocket)
    logger.info(f"[通知服务] 客户端连接: {client_id}")
    
    try:
        # 发送欢迎消息
        await websocket.send(json_encode({
            "type": "welcome",
            "service": "notification",
            "message": "通知服务已连接"
        }))
        
        # 定期推送通知
        counter = 1
        while True:
            await asyncio.sleep(5)
            
            notification = {
                "type": "notification",
                "id": counter,
                "title": f"通知 #{counter}",
                "message": f"这是第 {counter} 条通知",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json_encode(notification))
            logger.info(f"[通知服务] 发送通知 #{counter}")
            counter += 1
            
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"[通知服务] 客户端断开: {client_id}")
    except Exception as e:
        logger.error(f"[通知服务] 发生错误: {e}")


async def example_echo_handler(websocket: WebSocketServerProtocol):
    """
    示例：回显服务处理器
    简单地将收到的消息原样返回
    """
    logger.info(f"[回显服务] 客户端连接")
    
    try:
        await websocket.send(json_encode({
            "type": "welcome",
            "service": "echo",
            "message": "回显服务已连接，发送的消息将被原样返回"
        }))
        
        async for message in websocket:
            # 原样返回
            await websocket.send(message)
            logger.info(f"[回显服务] 回显: {message}")
            
    except Exception as e:
        logger.error(f"[回显服务] 发生错误: {e}")


# ==================== 主函数 ====================

async def main():
    """主函数"""
    # 创建服务器实例
    server = WebSocketServer(host="0.0.0.0", port=8765)
    
    # 注册自定义路由（可选）
    # 方式1: 直接注册
    server.register_route("/api/notifications", example_notification_handler)
    server.register_route("/echo", example_echo_handler)
    
    # 方式2: 使用装饰器（推荐）
    @server.route("/custom")
    async def handle_custom(websocket):
        """自定义路径处理器示例"""
        logger.info("[自定义服务] 客户端连接")
        await websocket.send(json_encode({
            "type": "welcome",
            "service": "custom",
            "message": "这是一个自定义服务"
        }))
        
        async for message in websocket:
            data = json.loads(message)
            logger.info(f"[自定义服务] 收到消息: {data}")
            
            # 自定义业务逻辑
            await websocket.send(json_encode({
                "type": "response",
                "original": data,
                "processed": "已处理"
            }))
    
    # 启动服务器
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
