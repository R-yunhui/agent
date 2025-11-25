"""
消息处理器模块
处理各种类型的 WebSocket 消息
"""
import logging
from typing import Dict, Any
from datetime import datetime
from connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class MessageHandler:
    """消息处理器类"""
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        初始化消息处理器
        
        Args:
            connection_manager: 连接管理器实例
        """
        self.conn_mgr = connection_manager
        
        # 消息类型到处理函数的映射
        self.handlers = {
            "chat": self.handle_chat,
            "private_chat": self.handle_private_chat,
            "join_room": self.handle_join_room,
            "leave_room": self.handle_leave_room,
            "room_chat": self.handle_room_chat,
            "get_online_users": self.handle_get_online_users,
            "get_rooms": self.handle_get_rooms,
            "get_room_members": self.handle_get_room_members,
            "custom_command": self.handle_custom_command,
            "pong": self.handle_pong,  # 心跳响应处理
        }
    
    async def handle_message(self, client_id: str, data: Dict[str, Any]):
        """
        处理客户端消息
        
        Args:
            client_id: 客户端ID
            data: 消息数据
        """
        message_type = data.get("type")
        
        if not message_type:
            await self._send_error(client_id, "消息类型不能为空")
            return
        
        # 查找对应的处理函数
        handler = self.handlers.get(message_type)
        
        if handler:
            try:
                await handler(client_id, data)
            except Exception as e:
                logger.error(f"处理消息 {message_type} 时发生错误: {e}", exc_info=True)
                await self._send_error(client_id, f"处理消息失败: {str(e)}")
        else:
            await self._send_error(client_id, f"未知的消息类型: {message_type}")
    
    async def handle_chat(self, client_id: str, data: Dict[str, Any]):
        """
        处理全局聊天消息
        
        Args:
            client_id: 客户端ID
            data: 消息数据，格式: {"type": "chat", "message": "消息内容"}
        """
        client = self.conn_mgr.get_client(client_id)
        if not client:
            return
        
        message_content = data.get("message", "")
        if not message_content:
            await self._send_error(client_id, "消息内容不能为空")
            return
        
        # 构建广播消息
        broadcast_message = {
            "type": "chat",
            "from": client.username,
            "message": message_content,
            "timestamp": datetime.now().isoformat()
        }
        
        # 广播给所有客户端（包括发送者）
        await self.conn_mgr.broadcast(broadcast_message)
        
        logger.info(f"全局聊天 - {client.username}: {message_content}")
    
    async def handle_private_chat(self, client_id: str, data: Dict[str, Any]):
        """
        处理私聊消息
        
        Args:
            client_id: 客户端ID
            data: 消息数据，格式: {"type": "private_chat", "to": "目标用户名", "message": "消息内容"}
        """
        client = self.conn_mgr.get_client(client_id)
        if not client:
            return
        
        target_username = data.get("to")
        message_content = data.get("message", "")
        
        if not target_username or not message_content:
            await self._send_error(client_id, "目标用户和消息内容不能为空")
            return
        
        # 查找目标用户
        target_client = self.conn_mgr.get_client_by_username(target_username)
        if not target_client:
            await self._send_error(client_id, f"用户 {target_username} 不在线")
            return
        
        # 构建私聊消息
        private_message = {
            "type": "private_chat",
            "from": client.username,
            "to": target_username,
            "message": message_content,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发送给目标用户
        await self.conn_mgr.send_to_client(target_client.client_id, private_message)
        
        # 发送确认给发送者
        await self.conn_mgr.send_to_client(client_id, {
            "type": "private_chat_sent",
            "to": target_username,
            "message": message_content,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"私聊 - {client.username} -> {target_username}: {message_content}")
    
    async def handle_join_room(self, client_id: str, data: Dict[str, Any]):
        """
        处理加入房间请求
        
        Args:
            client_id: 客户端ID
            data: 消息数据，格式: {"type": "join_room", "room": "房间名称"}
        """
        room_name = data.get("room")
        
        if not room_name:
            await self._send_error(client_id, "房间名称不能为空")
            return
        
        # 加入房间
        success = await self.conn_mgr.join_room(client_id, room_name)
        
        if success:
            client = self.conn_mgr.get_client(client_id)
            members = self.conn_mgr.get_room_members(room_name)
            
            # 发送成功消息
            await self.conn_mgr.send_to_client(client_id, {
                "type": "join_room_success",
                "room": room_name,
                "members": members,
                "message": f"成功加入房间 {room_name}"
            })
        else:
            await self._send_error(client_id, "加入房间失败")
    
    async def handle_leave_room(self, client_id: str, data: Dict[str, Any]):
        """
        处理离开房间请求
        
        Args:
            client_id: 客户端ID
            data: 消息数据，格式: {"type": "leave_room", "room": "房间名称"}
        """
        room_name = data.get("room")
        
        if not room_name:
            await self._send_error(client_id, "房间名称不能为空")
            return
        
        # 离开房间
        success = await self.conn_mgr.leave_room(client_id, room_name)
        
        if success:
            # 发送成功消息
            await self.conn_mgr.send_to_client(client_id, {
                "type": "leave_room_success",
                "room": room_name,
                "message": f"已离开房间 {room_name}"
            })
        else:
            await self._send_error(client_id, "离开房间失败")
    
    async def handle_room_chat(self, client_id: str, data: Dict[str, Any]):
        """
        处理房间聊天消息
        
        Args:
            client_id: 客户端ID
            data: 消息数据，格式: {"type": "room_chat", "room": "房间名称", "message": "消息内容"}
        """
        client = self.conn_mgr.get_client(client_id)
        if not client:
            return
        
        room_name = data.get("room")
        message_content = data.get("message", "")
        
        if not room_name or not message_content:
            await self._send_error(client_id, "房间名称和消息内容不能为空")
            return
        
        # 检查是否在房间内
        if room_name not in client.rooms:
            await self._send_error(client_id, f"您不在房间 {room_name} 内")
            return
        
        # 构建房间消息
        room_message = {
            "type": "room_chat",
            "room": room_name,
            "from": client.username,
            "message": message_content,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发送给房间内所有成员
        await self.conn_mgr.send_to_room(room_name, room_message)
        
        logger.info(f"房间聊天 [{room_name}] - {client.username}: {message_content}")
    
    async def handle_get_online_users(self, client_id: str, data: Dict[str, Any]):
        """
        处理获取在线用户列表请求
        
        Args:
            client_id: 客户端ID
            data: 消息数据
        """
        online_users = self.conn_mgr.get_online_users()
        
        await self.conn_mgr.send_to_client(client_id, {
            "type": "online_users",
            "users": online_users,
            "count": len(online_users)
        })
    
    async def handle_get_rooms(self, client_id: str, data: Dict[str, Any]):
        """
        处理获取所有房间列表请求
        
        Args:
            client_id: 客户端ID
            data: 消息数据
        """
        rooms = self.conn_mgr.get_all_rooms()
        
        await self.conn_mgr.send_to_client(client_id, {
            "type": "rooms",
            "rooms": [
                {"name": name, "members_count": count}
                for name, count in rooms.items()
            ]
        })
    
    async def handle_get_room_members(self, client_id: str, data: Dict[str, Any]):
        """
        处理获取房间成员列表请求
        
        Args:
            client_id: 客户端ID
            data: 消息数据，格式: {"type": "get_room_members", "room": "房间名称"}
        """
        room_name = data.get("room")
        
        if not room_name:
            await self._send_error(client_id, "房间名称不能为空")
            return
        
        members = self.conn_mgr.get_room_members(room_name)
        
        await self.conn_mgr.send_to_client(client_id, {
            "type": "room_members",
            "room": room_name,
            "members": members,
            "count": len(members)
        })
    
    async def handle_custom_command(self, client_id: str, data: Dict[str, Any]):
        """
        处理自定义命令
        这是一个示例，展示如何添加自定义业务逻辑
        
        Args:
            client_id: 客户端ID
            data: 消息数据，格式: {"type": "custom_command", "command": "命令名称", "params": {...}}
        """
        client = self.conn_mgr.get_client(client_id)
        if not client:
            return
        
        command = data.get("command")
        params = data.get("params", {})
        
        # 这里可以根据不同的命令执行不同的业务逻辑
        if command == "echo":
            # 简单的回显命令
            await self.conn_mgr.send_to_client(client_id, {
                "type": "command_result",
                "command": "echo",
                "result": params
            })
        elif command == "stats":
            # 获取服务器统计信息
            stats = {
                "online_users": len(self.conn_mgr.clients),
                "total_rooms": len(self.conn_mgr.rooms),
                "user_rooms": list(client.rooms)
            }
            await self.conn_mgr.send_to_client(client_id, {
                "type": "command_result",
                "command": "stats",
                "result": stats
            })
        else:
            await self._send_error(client_id, f"未知的命令: {command}")
        
        logger.info(f"自定义命令 - {client.username}: {command}")
    
    async def handle_pong(self, client_id: str, data: Dict[str, Any]):
        """
        处理客户端的心跳响应
        
        Args:
            client_id: 客户端ID
            data: 消息数据，格式: {"type": "pong", "ping_id": 123}
        """
        client = self.conn_mgr.get_client(client_id)
        if not client:
            return
        
        ping_id = data.get("ping_id")
        
        # 调用心跳处理器
        if 'pong_handler' in client.metadata:
            handler = client.metadata['pong_handler']
            await handler(ping_id)
            logger.debug(f"处理 pong 响应: {client.username}, ping_id: {ping_id}")
    
    async def _send_error(self, client_id: str, error_message: str):
        """
        发送错误消息
        
        Args:
            client_id: 客户端ID
            error_message: 错误消息
        """
        await self.conn_mgr.send_to_client(client_id, {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
        logger.warning(f"发送错误消息给 {client_id}: {error_message}")
