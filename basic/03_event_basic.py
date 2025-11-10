"""
PyPubSub 简单演示
安装: pip install pypubsub
"""

from pubsub import pub
import time


# ========== 定义监听器函数 ==========

def on_user_registered(user_id, username, email):
    """用户注册事件监听器1 - 发送欢迎邮件"""
    print(f"📧 [邮件服务] 发送欢迎邮件给: {email}")
    time.sleep(0.5)  # 模拟耗时操作
    print(f"   ✅ 邮件发送成功")


def on_user_registered_create_profile(user_id, username, email):
    """用户注册事件监听器2 - 创建用户档案"""
    print(f"👤 [档案服务] 为 {username} 创建用户档案")
    time.sleep(0.3)
    print(f"   ✅ 档案创建成功")


def on_user_registered_grant_points(user_id, username, email):
    """用户注册事件监听器3 - 赠送积分"""
    print(f"🎁 [积分服务] 为用户 {user_id} 赠送 100 新人积分")
    time.sleep(0.2)
    print(f"   ✅ 积分发放成功")


def on_order_created(order_id, user_id, amount):
    """订单创建事件监听器"""
    print(f"📦 [订单服务] 订单创建: {order_id}, 金额: ¥{amount}")


def on_order_paid(order_id, user_id, amount):
    """订单支付事件监听器1 - 发货"""
    print(f"🚚 [物流服务] 订单 {order_id} 准备发货")


def on_order_paid_send_receipt(order_id, user_id, amount):
    """订单支付事件监听器2 - 发送收据"""
    print(f"📄 [财务服务] 生成收据，金额: ¥{amount}")


def on_agent_task_started(task_id, query):
    """Agent 任务开始"""
    print(f"🤖 [Agent] 任务 {task_id} 开始处理: {query}")


def on_agent_task_completed(task_id, query, result, execution_time):
    """Agent 任务完成"""
    print(f"✅ [Agent] 任务 {task_id} 完成")
    print(f"   查询: {query}")
    print(f"   结果: {result}")
    print(f"   耗时: {execution_time:.2f}秒")


# ========== 注册监听器 ==========

print("=" * 60)
print("🎯 注册事件监听器...")
print("=" * 60)

# 用户注册事件 - 可以有多个监听器
"""
:arg1 listener: 事件监听器函数
:arg2 topic: 事件主题字符串
"""
pub.subscribe(on_user_registered, 'user.registered')
pub.subscribe(on_user_registered_create_profile, 'user.registered')
pub.subscribe(on_user_registered_grant_points, 'user.registered')

# 订单事件
pub.subscribe(on_order_created, 'order.created')
pub.subscribe(on_order_paid, 'order.paid')
pub.subscribe(on_order_paid_send_receipt, 'order.paid')

# Agent 事件
pub.subscribe(on_agent_task_started, 'agent.task.started')
pub.subscribe(on_agent_task_completed, 'agent.task.completed')

print("✅ 监听器注册完成\n")


# ========== 业务场景演示 ==========

def simulate_user_registration():
    """模拟用户注册"""
    print("\n" + "=" * 60)
    print("场景1: 用户注册")
    print("=" * 60)

    # 核心业务逻辑
    user_id = 10001
    username = "张三"
    email = "zhangsan@example.com"

    print(f"💾 [用户服务] 用户 {username} 注册成功, ID: {user_id}\n")

    # 发布事件 - 所有订阅了该事件的监听器都会被触发
    """
    :arg1 topicName: 事件主题字符串
    :arg2 **msgData: 事件消息数据
    """
    pub.sendMessage(
        'user.registered',
        user_id=user_id,
        username=username,
        email=email
    )

    print(f"\n🎉 用户注册流程完成!")


def simulate_order_process():
    """模拟订单处理流程"""
    print("\n" + "=" * 60)
    print("场景2: 订单处理")
    print("=" * 60)

    order_id = "ORD20240001"
    user_id = 10001
    amount = 299.99

    # 1. 创建订单
    print(f"💾 [订单服务] 创建订单...")
    pub.sendMessage('order.created', order_id=order_id, user_id=user_id, amount=amount)

    print(f"\n⏳ 等待用户支付...\n")
    time.sleep(1)

    # 2. 支付成功
    print(f"💳 [支付服务] 支付成功!\n")
    pub.sendMessage('order.paid', order_id=order_id, user_id=user_id, amount=amount)

    print(f"\n🎉 订单处理完成!")


def simulate_agent_task():
    """模拟 Agent 任务执行"""
    print("\n" + "=" * 60)
    print("场景3: Agent 任务执行")
    print("=" * 60)

    task_id = "TASK_001"
    query = "帮我总结今天的新闻"

    # 触发任务开始事件
    pub.sendMessage('agent.task.started', task_id=task_id, query=query)

    print()

    # 模拟 Agent 执行
    start_time = time.time()
    time.sleep(1.5)  # 模拟处理时间
    result = "今天的主要新闻包括: 1. AI技术突破... 2. 经济政策更新..."
    execution_time = time.time() - start_time

    print()

    # 触发任务完成事件
    pub.sendMessage(
        'agent.task.completed',
        task_id=task_id,
        query=query,
        result=result,
        execution_time=execution_time
    )

    print(f"\n🎉 Agent 任务执行完成!")


# ========== 层级主题演示 ==========

def on_any_user_event(topic=pub.AUTO_TOPIC, **kwargs):
    """捕获所有 user.* 事件"""
    print(f"🎯 [监控] 捕获到用户事件: {topic.getName()}")


def simulate_topic_hierarchy():
    """演示层级主题"""
    print("\n" + "=" * 60)
    print("场景4: 层级主题监听")
    print("=" * 60)

    # 注册一个监听所有 user.* 事件的监听器
    pub.subscribe(on_any_user_event, 'user')

    print("🔧 注册了一个监听所有 'user.*' 事件的监听器\n")

    # 触发不同的用户事件
    pub.sendMessage('user.registered', user_id=1, username='李四', email='lisi@example.com')
    print()
    pub.sendMessage('user.login', user_id=1, username='李四')
    print()
    pub.sendMessage('user.logout', user_id=1, username='李四')


# ========== 取消订阅演示 ==========

def simulate_unsubscribe():
    """演示取消订阅"""
    print("\n" + "=" * 60)
    print("场景5: 取消订阅")
    print("=" * 60)

    def temp_listener(order_id, user_id, amount):
        print(f"⚡ [临时监听器] 收到订单: {order_id}")

    # 订阅
    pub.subscribe(temp_listener, 'order.created')
    print("✅ 添加临时监听器")

    pub.sendMessage('order.created', order_id='TEST001', user_id=999, amount=100)

    print()

    # 取消订阅
    pub.unsubscribe(temp_listener, 'order.created')
    print("❌ 移除临时监听器\n")

    pub.sendMessage('order.created', order_id='TEST002', user_id=999, amount=200)
    print("   (临时监听器不再触发)")


# ========== 主程序 ==========

if __name__ == "__main__":
    # 运行各个场景
    simulate_user_registration()

    # simulate_order_process()
    #
    # simulate_agent_task()
    #
    # simulate_topic_hierarchy()
    #
    # simulate_unsubscribe()

    print("\n" + "=" * 60)
    print("✅ 所有演示完成!")
    print("=" * 60)
