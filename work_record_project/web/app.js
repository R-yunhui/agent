const { createApp, ref, reactive, watch, nextTick, onMounted } = Vue;
const { ElMessage, ElLoading } = ElementPlus;

const app = createApp({
    setup() {
        // ==================== 状态定义 ====================
        const loading = ref(false);
        const generatedReport = ref('');
        const mainTab = ref('chat'); // chat | daily | weekly

        // 日报表单数据
        const form = reactive({
            record_date: new Date().toISOString().split('T')[0],
            project: '',
            tomorrow: '',
            product: '',
            others: '',
            risks: ''
        });

        // 周报表单数据
        const weeklyForm = reactive({
            dateRange: []
        });

        // ==================== 聊天相关状态 ====================
        const chatInput = ref('');
        const chatMessages = ref([]);
        const isAiTyping = ref(false);
        const chatSessionId = ref('');
        const chatMessagesRef = ref(null);

        // 生成会话 ID
        const generateSessionId = () => {
            return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        };

        // 初始化会话 ID
        chatSessionId.value = generateSessionId();

        // API 基础地址
        const API_BASE_URL = 'http://localhost:8000/api';

        // ==================== 工具函数 ====================
        
        // 获取本周一的日期
        const getMonday = (d) => {
            const date = new Date(d);
            const day = date.getDay();
            const diff = date.getDate() - day + (day === 0 ? -6 : 1);
            return new Date(date.setDate(diff));
        };

        // 格式化日期为 YYYY-MM-DD
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };

        // 滚动到聊天底部
        const scrollToBottom = async () => {
            await nextTick();
            if (chatMessagesRef.value) {
                chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
            }
        };

        // ==================== 日期快捷选项 ====================
        const dateShortcuts = [
            {
                text: '本周',
                value: () => {
                    const today = new Date();
                    const monday = getMonday(today);
                    return [monday, today];
                }
            },
            {
                text: '上周',
                value: () => {
                    const today = new Date();
                    const thisMonday = getMonday(today);
                    const lastMonday = new Date(thisMonday);
                    lastMonday.setDate(lastMonday.getDate() - 7);
                    const lastSunday = new Date(thisMonday);
                    lastSunday.setDate(lastSunday.getDate() - 1);
                    return [lastMonday, lastSunday];
                }
            },
            {
                text: '最近7天',
                value: () => {
                    const today = new Date();
                    const sevenDaysAgo = new Date(today);
                    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6);
                    return [sevenDaysAgo, today];
                }
            },
            {
                text: '最近14天',
                value: () => {
                    const today = new Date();
                    const fourteenDaysAgo = new Date(today);
                    fourteenDaysAgo.setDate(fourteenDaysAgo.getDate() - 13);
                    return [fourteenDaysAgo, today];
                }
            },
            {
                text: '本月',
                value: () => {
                    const today = new Date();
                    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                    return [firstDay, today];
                }
            }
        ];

        // 初始化周报日期为本周
        const initThisWeek = () => {
            const today = new Date();
            const monday = getMonday(today);
            weeklyForm.dateRange = [formatDate(monday), formatDate(today)];
        };
        initThisWeek();

        // ==================== 聊天功能 ====================
        
        // 发送聊天消息
        const sendChatMessage = async () => {
            const message = chatInput.value.trim();
            if (!message || isAiTyping.value) return;

            // 添加用户消息
            chatMessages.value.push({
                role: 'user',
                content: message
            });
            chatInput.value = '';
            isAiTyping.value = true;
            scrollToBottom();

            // 添加 AI 消息占位
            const aiMessageIndex = chatMessages.value.length;
            chatMessages.value.push({
                role: 'ai',
                content: ''
            });

            try {
                // 使用 fetch 发送 SSE 请求
                const response = await fetch(`${API_BASE_URL}/chat/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: message,
                        session_id: chatSessionId.value
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                // 读取 SSE 流
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                
                                if (data.type === 'start') {
                                    // 更新 session_id（如果服务器返回了新的）
                                    if (data.session_id) {
                                        chatSessionId.value = data.session_id;
                                    }
                                } else if (data.type === 'content' && data.content) {
                                    // 追加内容
                                    chatMessages.value[aiMessageIndex].content += data.content;
                                    scrollToBottom();
                                } else if (data.type === 'end') {
                                    // 结束
                                    isAiTyping.value = false;
                                } else if (data.type === 'error') {
                                    throw new Error(data.message || '未知错误');
                                }
                            } catch (e) {
                                // 忽略 JSON 解析错误（可能是空行）
                                if (line.slice(6).trim()) {
                                    console.warn('Parse error:', e);
                                }
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Chat error:', error);
                chatMessages.value[aiMessageIndex].content = '❌ 抱歉，发生错误：' + error.message;
                ElMessage.error('发送失败：' + error.message);
            } finally {
                isAiTyping.value = false;
                scrollToBottom();
            }
        };

        // 发送快捷消息
        const sendQuickMessage = (message) => {
            chatInput.value = message;
            sendChatMessage();
        };

        // 清空聊天历史
        const clearChatHistory = () => {
            chatMessages.value = [];
            chatSessionId.value = generateSessionId();
            ElMessage.success('对话已清空');
        };

        // ==================== 日报相关 ====================
        
        // 提交工作记录
        const submitRecord = async () => {
            if (!form.project || !form.tomorrow) {
                ElMessage.warning('请填写必填项：项目工作和次日计划');
                return null;
            }

            try {
                loading.value = true;
                const response = await axios.post(`${API_BASE_URL}/records/`, form);
                ElMessage.success('工作记录保存成功！');
                return response.data;
            } catch (error) {
                console.error(error);
                ElMessage.error('保存失败：' + (error.response?.data?.detail || error.message));
                return null;
            } finally {
                loading.value = false;
            }
        };

        // 生成日报
        const generateDailyReport = async () => {
            const saved = await submitRecord();
            if (!saved) return;

            let loadingInstance = null;
            try {
                loadingInstance = ElLoading.service({
                    text: '正在调用大模型生成日报，请稍候...',
                    background: 'rgba(0, 0, 0, 0.7)'
                });

                const response = await axios.post(
                    `${API_BASE_URL}/records/daily/generate?record_date=${form.record_date}`
                );

                generatedReport.value = response.data;
                ElMessage.success('日报生成成功！');
            } catch (error) {
                console.error(error);
                ElMessage.error('生成失败：' + (error.response?.data?.detail || error.message));
            } finally {
                if (loadingInstance) loadingInstance.close();
            }
        };

        // ==================== 周报相关 ====================
        
        // 生成周报
        const generateWeeklyReport = async () => {
            if (!weeklyForm.dateRange || weeklyForm.dateRange.length !== 2) {
                ElMessage.warning('请选择日期范围');
                return;
            }

            const [startDate, endDate] = weeklyForm.dateRange;

            let loadingInstance = null;
            try {
                loadingInstance = ElLoading.service({
                    text: '正在调用大模型生成周报，请稍候...',
                    background: 'rgba(0, 0, 0, 0.7)'
                });

                const response = await axios.post(
                    `${API_BASE_URL}/records/weekly/generate?start_date=${startDate}&end_date=${endDate}`
                );

                generatedReport.value = response.data;
                ElMessage.success('周报生成成功！');
            } catch (error) {
                console.error(error);
                ElMessage.error('生成失败：' + (error.response?.data?.detail || error.message));
            } finally {
                if (loadingInstance) loadingInstance.close();
            }
        };

        // ==================== 通用功能 ====================
        
        // 复制报告内容
        const copyReport = () => {
            if (!generatedReport.value) return;
            navigator.clipboard.writeText(generatedReport.value).then(() => {
                ElMessage.success('复制成功！');
            }).catch(() => {
                ElMessage.error('复制失败，请手动复制');
            });
        };

        // 渲染 Markdown
        const renderMarkdown = (content) => {
            if (!content) return '';
            if (typeof marked === 'undefined') {
                console.warn('Marked library not loaded, falling back to raw text');
                return '<pre>' + content + '</pre>';
            }
            return marked.parse(content);
        };

        // 切换 Tab 时清空报告预览（不清空聊天）
        watch(mainTab, (newTab) => {
            if (newTab !== 'chat') {
                generatedReport.value = '';
            }
        });

        // ==================== 返回 ====================
        return {
            // 主状态
            mainTab,
            loading,
            generatedReport,
            // 日报
            form,
            submitRecord,
            generateDailyReport,
            // 周报
            weeklyForm,
            dateShortcuts,
            generateWeeklyReport,
            // 聊天
            chatInput,
            chatMessages,
            chatMessagesRef,
            isAiTyping,
            sendChatMessage,
            sendQuickMessage,
            clearChatHistory,
            // 通用
            copyReport,
            renderMarkdown
        };
    }
});

// 使用中文语言包
app.use(ElementPlus, {
    locale: ElementPlusLocaleZhCn
});
app.mount('#app');
