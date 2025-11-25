"""
WebSocket 测试客户端
支持测试所有功能：聊天服务、自定义路径、JSON/文本格式
"""
import asyncio
import json
import logging
from typing import Optional, Any

import websockets

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# JSON 编码辅助函数，确保中文正常显示
def json_encode(data: dict) -> str:
    """JSON 编码，支持中文"""
    return json.dumps(data, ensure_ascii=False)


class WebSocketClient:
    """WebSocket 客户端类"""
    
    def __init__(self, uri: str = "ws://localhost:8765/chat", username: str = "TestUser"):
        """
        初始化客户端
        
        Args:
            uri: WebSocket 服务器地址（包含路径）
            username: 用户名
        """
        self.uri = uri
        self.username = username
        self.websocket: Optional[Any] = None
        self.client_id: Optional[str] = None
    
    async def connect(self, use_json: bool = True):
        """
        连接到服务器
        
        Args:
            use_json: True=使用JSON格式认证, False=使用文本格式认证
        
        Returns:
            是否连接成功
        """
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"✓ 已连接到: {self.uri}")
            
            # 发送认证消息
            if use_json:
                # JSON 格式认证
                auth_msg = json_encode({"type": "auth", "username": self.username})
                await self.websocket.send(auth_msg)
                logger.info(f"→ 发送认证 (JSON): {auth_msg}")
            else:
                # 纯文本格式认证
                await self.websocket.send(self.username)
                logger.info(f"→ 发送认证 (文本): {self.username}")
            
            # 等待认证响应
            response = await self.websocket.recv()
            logger.info(f"← 收到响应: {response}")
            
            # 尝试解析响应
            try:
                data = json.loads(response)
                if data.get("type") == "auth_success":
                    self.client_id = data.get("client_id")
                    logger.info(f"✓ 认证成功! 客户端ID: {self.client_id}\n")
                    return True
            except json.JSONDecodeError:
                logger.info(f"✓ 连接成功 (非聊天服务)\n")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"✗ 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            logger.info("✓ 已断开连接\n")
    
    async def send_text(self, text: str):
        """
        发送纯文本消息
        
        Args:
            text: 文本内容
        """
        if not self.websocket:
            logger.error("✗ 未连接到服务器")
            return
        
        await self.websocket.send(text)
        logger.info(f"→ 发送文本: {text}")
    
    async def send_json(self, data: dict):
        """
        发送 JSON 消息
        
        Args:
            data: 消息字典
        """
        if not self.websocket:
            logger.error("✗ 未连接到服务器")
            return
        
        msg = json_encode(data)
        await self.websocket.send(msg)
        logger.info(f"→ 发送JSON: {msg}")
    
    async def receive_messages(self, count: int = 1):
        """
        接收指定数量的消息
        
        Args:
            count: 接收消息数量
        """
        for i in range(count):
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=5)
                logger.info(f"← 收到消息: {message}")
            except asyncio.TimeoutError:
                logger.warning("⚠ 接收消息超时")
                break
            except Exception as e:
                logger.error(f"✗ 接收消息失败: {e}")
                break
    
    async def listen_forever(self):
        """持续监听消息"""
        try:
            async for message in self.websocket:
                try:
                    # 尝试解析 JSON
                    data = json.loads(message)
                    
                    # 自动响应心跳 ping
                    if data.get("type") == "ping":
                        ping_id = data.get("ping_id")
                        # 立即回复 pong
                        await self.send_json({"type": "pong", "ping_id": ping_id})
                        logger.debug(f"← 收到心跳 PING (#{ping_id}), 已回复 PONG")
                    else:
                        # 普通消息，打印
                        logger.info(f"← 收到消息: {message}")
                
                except json.JSONDecodeError:
                    # 非 JSON 消息
                    logger.info(f"← 收到消息: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("✓ 连接已关闭")
        except Exception as e:
            logger.error(f"✗ 监听错误: {e}")



# ==================== 测试场景 ====================

async def test_text_format():
    """测试纯文本格式（聊天服务）"""
    print("\n" + "="*60)
    print("测试 1: 纯文本格式聊天")
    print("="*60 + "\n")
    
    client = WebSocketClient(username="文本用户")
    
    if await client.connect(use_json=False):
        # 发送纯文本消息
        await client.send_text("你好，这是纯文本消息！")
        await client.receive_messages(1)
        
        await asyncio.sleep(0.5)
        
        await client.send_text("不需要 JSON，直接发文本就行")
        await client.receive_messages(1)
        
        await client.disconnect()


async def test_json_format():
    """测试 JSON 格式（聊天服务）"""
    print("\n" + "="*60)
    print("测试 2: JSON 格式聊天")
    print("="*60 + "\n")
    
    client = WebSocketClient(username="JSON用户")
    
    if await client.connect(use_json=True):
        # 发送 JSON 格式聊天消息
        await client.send_json({"type": "chat", "message": "你好，这是JSON消息"})
        await client.receive_messages(1)
        
        await asyncio.sleep(0.5)
        
        # 查询在线用户
        await client.send_json({"type": "get_online_users"})
        await client.receive_messages(1)
        
        await client.disconnect()


async def test_room_features():
    """测试房间功能"""
    print("\n" + "="*60)
    print("测试 3: 房间管理功能")
    print("="*60 + "\n")
    
    client = WebSocketClient(username="房间测试用户")
    
    if await client.connect(use_json=True):
        # 加入房间
        await client.send_json({"type": "join_room", "room": "技术讨论"})
        await client.receive_messages(1)
        
        await asyncio.sleep(0.5)
        
        # 在房间发送消息
        await client.send_json({
            "type": "room_chat",
            "room": "技术讨论",
            "message": "大家好，我是新来的！"
        })
        await client.receive_messages(1)
        
        await asyncio.sleep(0.5)
        
        # 获取房间成员
        await client.send_json({"type": "get_room_members", "room": "技术讨论"})
        await client.receive_messages(1)
        
        await asyncio.sleep(0.5)
        
        # 离开房间
        await client.send_json({"type": "leave_room", "room": "技术讨论"})
        await client.receive_messages(1)
        
        await client.disconnect()


async def test_private_chat():
    """测试私聊功能（需要两个客户端）"""
    print("\n" + "="*60)
    print("测试 4: 私聊功能")
    print("="*60 + "\n")
    
    # 创建两个客户端
    alice = WebSocketClient(username="Alice")
    bob = WebSocketClient(username="Bob")
    
    # 连接两个客户端
    if await alice.connect() and await bob.connect():
        # Alice 给 Bob 发私聊
        await alice.send_json({
            "type": "private_chat",
            "to": "Bob",
            "message": "嗨 Bob，这是私密消息"
        })
        
        # Bob 接收消息
        await bob.receive_messages(1)
        
        await asyncio.sleep(0.5)
        
        # Bob 回复 Alice
        await bob.send_json({
            "type": "private_chat",
            "to": "Alice",
            "message": "收到！Alice"
        })
        
        # Alice 接收回复
        await alice.receive_messages(1)
        
        await alice.disconnect()
        await bob.disconnect()


async def test_notification_service():
    """测试通知服务路径"""
    print("\n" + "="*60)
    print("测试 5: 通知服务 (/api/notifications)")
    print("="*60 + "\n")
    
    client = WebSocketClient(
        uri="ws://localhost:8765/api/notifications",
        username="通知测试用户"
    )
    
    if await client.connect(use_json=False):
        # 接收 3 条通知
        logger.info("等待接收通知...")
        await client.receive_messages(3)
        await client.disconnect()


async def test_echo_service():
    """测试回显服务路径"""
    print("\n" + "="*60)
    print("测试 6: 回显服务 (/echo)")
    print("="*60 + "\n")
    
    client = WebSocketClient(
        uri="ws://localhost:8765/echo",
        username="回显测试用户"
    )
    
    if await client.connect(use_json=False):
        # 发送几条消息
        await client.send_text("测试消息 1")
        await client.receive_messages(1)
        
        await asyncio.sleep(0.3)
        
        await client.send_text("测试消息 2")
        await client.receive_messages(1)
        
        await client.disconnect()


async def test_custom_service():
    """测试自定义服务路径"""
    print("\n" + "="*60)
    print("测试 7: 自定义服务 (/custom)")
    print("="*60 + "\n")
    
    client = WebSocketClient(
        uri="ws://localhost:8765/custom",
        username="自定义测试用户"
    )
    
    if await client.connect(use_json=False):
        # 发送 JSON 消息
        await client.send_json({"action": "test", "data": "hello"})
        await client.receive_messages(1)
        
        await client.disconnect()


async def run_interactive_mode():
    """交互式模式"""
    print("\n" + "="*60)
    print("WebSocket 交互式客户端")
    print("="*60)
    
    # 选择路径
    print("\n可用路径:")
    print("  1. /chat              - 聊天服务（默认）")
    print("  2. /api/notifications - 通知服务")
    print("  3. /echo              - 回显服务")
    print("  4. /custom            - 自定义服务")
    print("  5. 自定义路径")
    
    choice = input("\n请选择路径 (1-5, 默认1): ").strip() or "1"
    
    path_map = {
        "1": "/chat",
        "2": "/api/notifications",
        "3": "/echo",
        "4": "/custom"
    }
    
    if choice == "5":
        path = input("请输入自定义路径 (如 /my/path): ").strip()
    else:
        path = path_map.get(choice, "/chat")
    
    # 输入用户名
    username = input("请输入用户名 (默认 TestUser): ").strip() or "TestUser"
    
    # 选择格式
    use_json = input("使用 JSON 格式? (y/n, 默认y): ").strip().lower() != 'n'
    
    # 创建客户端并连接
    uri = f"ws://localhost:8765{path}"
    client = WebSocketClient(uri=uri, username=username)
    
    if not await client.connect(use_json=use_json):
        return
    
    # 启动消息接收任务
    receive_task = asyncio.create_task(client.listen_forever())
    
    # 显示帮助
    print("\n" + "="*60)
    print("命令帮助:")
    print("  <文本>                     - 发送纯文本消息")
    print("  json <JSON内容>            - 发送JSON消息")
    print("  chat <消息>                - 发送聊天消息 (JSON)")
    print("  private <用户名> <消息>    - 发送私聊 (JSON)")
    print("  join <房间>                - 加入房间 (JSON)")
    print("  room <房间> <消息>         - 房间聊天 (JSON)")
    print("  users                      - 查询在线用户 (JSON)")
    print("  quit/exit                  - 退出")
    print("="*60 + "\n")
    
    try:
        while True:
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, ">>> "
            )
            
            if not user_input.strip():
                continue
            
            parts = user_input.strip().split(maxsplit=1)
            cmd = parts[0].lower()
            
            if cmd in ["quit", "exit"]:
                break
            
            elif cmd == "json" and len(parts) > 1:
                try:
                    data = json.loads(parts[1])
                    await client.send_json(data)
                except json.JSONDecodeError:
                    print("✗ 无效的 JSON 格式")
            
            elif cmd == "chat" and len(parts) > 1:
                await client.send_json({"type": "chat", "message": parts[1]})
            
            elif cmd == "private":
                sub_parts = parts[1].split(maxsplit=1) if len(parts) > 1 else []
                if len(sub_parts) == 2:
                    await client.send_json({
                        "type": "private_chat",
                        "to": sub_parts[0],
                        "message": sub_parts[1]
                    })
                else:
                    print("用法: private <用户名> <消息>")
            
            elif cmd == "join" and len(parts) > 1:
                await client.send_json({"type": "join_room", "room": parts[1]})
            
            elif cmd == "room":
                sub_parts = parts[1].split(maxsplit=1) if len(parts) > 1 else []
                if len(sub_parts) == 2:
                    await client.send_json({
                        "type": "room_chat",
                        "room": sub_parts[0],
                        "message": sub_parts[1]
                    })
                else:
                    print("用法: room <房间> <消息>")
            
            elif cmd == "users":
                await client.send_json({"type": "get_online_users"})
            
            else:
                # 当作纯文本发送
                await client.send_text(user_input)
    
    except KeyboardInterrupt:
        print("\n收到中断信号")
    finally:
        receive_task.cancel()
        await client.disconnect()


async def run_all_tests():
    """运行所有自动化测试"""
    print("\n" + "="*60)
    print("开始运行所有测试...")
    print("请确保服务器已启动: python websocket/server.py")
    print("="*60)
    
    await asyncio.sleep(1)
    
    tests = [
        test_text_format,
        test_json_format,
        test_room_features,
        test_private_chat,
        test_notification_service,
        test_echo_service,
        test_custom_service,
    ]
    
    for test in tests:
        try:
            await test()
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"测试失败: {e}")
    
    print("\n" + "="*60)
    print("所有测试完成!")
    print("="*60 + "\n")


async def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "auto":
            await run_all_tests()
        elif mode == "text":
            await test_text_format()
        elif mode == "json":
            await test_json_format()
        elif mode == "room":
            await test_room_features()
        elif mode == "private":
            await test_private_chat()
        elif mode == "notify":
            await test_notification_service()
        elif mode == "echo":
            await test_echo_service()
        elif mode == "custom":
            await test_custom_service()
        else:
            print("用法:")
            print("  python client.py              - 交互式模式")
            print("  python client.py auto         - 运行所有测试")
            print("  python client.py text         - 测试纯文本格式")
            print("  python client.py json         - 测试JSON格式")
            print("  python client.py room         - 测试房间功能")
            print("  python client.py private      - 测试私聊")
            print("  python client.py notify       - 测试通知服务")
            print("  python client.py echo         - 测试回显服务")
            print("  python client.py custom       - 测试自定义服务")
    else:
        await run_interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n客户端已停止")
