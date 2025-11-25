"""
连接管理器模块
负责管理 WebSocket 连接、用户、房间等
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from dataclasses import dataclass, field
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


# JSON 编码辅助函数，确保中文正常显示
def json_encode(data: dict) -> str:
    """JSON 编码，支持中文"""
    return json.dumps(data, ensure_ascii=False)


@dataclass
class Client:
    """客户端信息类"""
    client_id: str
    websocket: WebSocketServerProtocol
    username: str
    connected_at: datetime = field(default_factory=datetime.now)
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "client_id": self.client_id,
            "username": self.username,
            "connected_at": self.connected_at.isoformat(),
            "rooms": list(self.rooms),
            "metadata": self.metadata
        }


class ConnectionManager:
    """连接管理器类"""
    
    def __init__(self):
        """初始化连接管理器"""
        # 存储所有客户端连接 {client_id: Client}
        self.clients: Dict[str, Client] = {}
        
        # 用户名到客户端ID的映射 {username: client_id}
        self.username_to_id: Dict[str, str] = {}
        
        # 房间管理 {room_name: Set[client_id]}
        self.rooms: Dict[str, Set[str]] = {}
        
        # 全局锁，用于并发控制
        self.lock = asyncio.Lock()
    
    async def register(self, websocket: WebSocketServerProtocol, username: str) -> str:
        """
        注册新客户端
        
        Args:
            websocket: WebSocket 连接对象
            username: 用户名
            
        Returns:
            客户端ID
        """
        async with self.lock:
            # 生成唯一的客户端ID
            client_id = f"client_{id(websocket)}_{datetime.now().timestamp()}"
            
            # 检查用户名是否已存在
            if username in self.username_to_id:
                # 如果用户名已存在，先断开旧连接
                old_client_id = self.username_to_id[username]
                if old_client_id in self.clients:
                    logger.warning(f"用户名 {username} 已存在，断开旧连接")
                    await self._force_disconnect(old_client_id)
            
            # 创建客户端对象
            client = Client(
                client_id=client_id,
                websocket=websocket,
                username=username
            )
            
            # 保存客户端信息
            self.clients[client_id] = client
            self.username_to_id[username] = client_id
            
            logger.info(f"注册客户端: {client_id}, 用户名: {username}")
            
            # 广播用户上线消息
            await self.broadcast_system_message(
                f"用户 {username} 已上线",
                exclude_clients={client_id}
            )
            
            return client_id
    
    async def unregister(self, client_id: str):
        """
        注销客户端
        
        Args:
            client_id: 客户端ID
        """
        async with self.lock:
            if client_id not in self.clients:
                return
            
            client = self.clients[client_id]
            username = client.username
            
            # 从所有房间移除
            for room_name in list(client.rooms):
                await self._leave_room_unsafe(client_id, room_name)
            
            # 移除客户端
            del self.clients[client_id]
            if username in self.username_to_id:
                del self.username_to_id[username]
            
            logger.info(f"注销客户端: {client_id}, 用户名: {username}")
            
            # 广播用户下线消息
            await self.broadcast_system_message(f"用户 {username} 已下线")
    
    async def _force_disconnect(self, client_id: str):
        """
        强制断开客户端连接（内部方法，调用前需加锁）
        
        Args:
            client_id: 客户端ID
        """
        if client_id in self.clients:
            client = self.clients[client_id]
            try:
                await client.websocket.send(json_encode({
                    "type": "system",
                    "message": "您的账号在其他地方登录，当前连接已断开"
                }))
                await client.websocket.close()
            except Exception as e:
                logger.error(f"强制断开连接失败: {e}")
    
    async def send_to_client(self, client_id: str, message: Dict):
        """
        发送消息给指定客户端
        
        Args:
            client_id: 客户端ID
            message: 消息内容
        """
        if client_id not in self.clients:
            logger.warning(f"客户端不存在: {client_id}")
            return
        
        client = self.clients[client_id]
        try:
            await client.websocket.send(json_encode(message))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            await self.unregister(client_id)
    
    async def broadcast(self, message: Dict, exclude_clients: Optional[Set[str]] = None):
        """
        广播消息给所有客户端
        
        Args:
            message: 消息内容
            exclude_clients: 排除的客户端ID集合
        """
        exclude_clients = exclude_clients or set()
        
        # 获取需要发送的客户端列表
        target_clients = [
            client_id for client_id in self.clients.keys()
            if client_id not in exclude_clients
        ]
        
        # 并发发送消息
        await asyncio.gather(
            *[self.send_to_client(client_id, message) for client_id in target_clients],
            return_exceptions=True
        )
    
    async def broadcast_system_message(self, msg: str, exclude_clients: Optional[Set[str]] = None):
        """
        广播系统消息
        
        Args:
            msg: 消息内容
            exclude_clients: 排除的客户端ID集合
        """
        message = {
            "type": "system",
            "message": msg,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message, exclude_clients)
    
    async def join_room(self, client_id: str, room_name: str) -> bool:
        """
        加入房间
        
        Args:
            client_id: 客户端ID
            room_name: 房间名称
            
        Returns:
            是否成功加入
        """
        async with self.lock:
            return await self._join_room_unsafe(client_id, room_name)
    
    async def _join_room_unsafe(self, client_id: str, room_name: str) -> bool:
        """
        加入房间（内部方法，调用前需加锁）
        """
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        
        # 创建房间（如果不存在）
        if room_name not in self.rooms:
            self.rooms[room_name] = set()
        
        # 加入房间
        self.rooms[room_name].add(client_id)
        client.rooms.add(room_name)
        
        logger.info(f"客户端 {client.username} 加入房间: {room_name}")
        
        # 通知房间内其他成员
        await self.send_to_room(
            room_name,
            {
                "type": "room_join",
                "room": room_name,
                "username": client.username,
                "message": f"{client.username} 加入了房间"
            },
            exclude_clients={client_id}
        )
        
        return True
    
    async def leave_room(self, client_id: str, room_name: str) -> bool:
        """
        离开房间
        
        Args:
            client_id: 客户端ID
            room_name: 房间名称
            
        Returns:
            是否成功离开
        """
        async with self.lock:
            return await self._leave_room_unsafe(client_id, room_name)
    
    async def _leave_room_unsafe(self, client_id: str, room_name: str) -> bool:
        """
        离开房间（内部方法，调用前需加锁）
        """
        if client_id not in self.clients or room_name not in self.rooms:
            return False
        
        client = self.clients[client_id]
        
        # 离开房间
        self.rooms[room_name].discard(client_id)
        client.rooms.discard(room_name)
        
        # 如果房间为空，删除房间
        if not self.rooms[room_name]:
            del self.rooms[room_name]
            logger.info(f"房间 {room_name} 已删除（无成员）")
        else:
            # 通知房间内其他成员
            await self.send_to_room(
                room_name,
                {
                    "type": "room_leave",
                    "room": room_name,
                    "username": client.username,
                    "message": f"{client.username} 离开了房间"
                }
            )
        
        logger.info(f"客户端 {client.username} 离开房间: {room_name}")
        return True
    
    async def send_to_room(
        self,
        room_name: str,
        message: Dict,
        exclude_clients: Optional[Set[str]] = None
    ):
        """
        发送消息给房间内所有成员
        
        Args:
            room_name: 房间名称
            message: 消息内容
            exclude_clients: 排除的客户端ID集合
        """
        if room_name not in self.rooms:
            return
        
        exclude_clients = exclude_clients or set()
        
        # 获取房间成员
        target_clients = [
            client_id for client_id in self.rooms[room_name]
            if client_id not in exclude_clients
        ]
        
        # 并发发送消息
        await asyncio.gather(
            *[self.send_to_client(client_id, message) for client_id in target_clients],
            return_exceptions=True
        )
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """获取客户端信息"""
        return self.clients.get(client_id)
    
    def get_client_by_username(self, username: str) -> Optional[Client]:
        """根据用户名获取客户端信息"""
        client_id = self.username_to_id.get(username)
        if client_id:
            return self.clients.get(client_id)
        return None
    
    def get_online_users(self) -> list:
        """获取所有在线用户列表"""
        return [
            {
                "username": client.username,
                "connected_at": client.connected_at.isoformat()
            }
            for client in self.clients.values()
        ]
    
    def get_room_members(self, room_name: str) -> list:
        """获取房间成员列表"""
        if room_name not in self.rooms:
            return []
        
        return [
            self.clients[client_id].username
            for client_id in self.rooms[room_name]
            if client_id in self.clients
        ]
    
    def get_all_rooms(self) -> Dict[str, int]:
        """获取所有房间及成员数量"""
        return {
            room_name: len(members)
            for room_name, members in self.rooms.items()
        }
