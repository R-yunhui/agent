const { createApp, ref, reactive, watch } = Vue;
const { ElMessage, ElLoading } = ElementPlus;

const app = createApp({
    setup() {
        // ==================== 状态定义 ====================
        const loading = ref(false);
        const generatedReport = ref('');
        const activeTab = ref('daily'); // daily | weekly

        // 日报表单数据
        const form = reactive({
            record_date: new Date().toISOString().split('T')[0],
            project: '',
            tomorrow: '',
            product: '',
            others: '',
            risks: ''
        });

        // 周报表单数据（使用日期范围数组 [开始日期, 结束日期]）
        const weeklyForm = reactive({
            dateRange: []
        });

        // API 基础地址
        const API_BASE_URL = 'http://localhost:8000/api';

        // ==================== 工具函数 ====================
        
        // 获取本周一的日期
        const getMonday = (d) => {
            const date = new Date(d);
            const day = date.getDay();
            const diff = date.getDate() - day + (day === 0 ? -6 : 1); // 调整周日
            return new Date(date.setDate(diff));
        };

        // 格式化日期为 YYYY-MM-DD
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };

        // ==================== 日期快捷选项（用于日期范围选择器） ====================
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
            // 先保存记录
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
            // 验证日期范围
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
                const errorMsg = error.response?.data?.detail || error.message;
                ElMessage.error('生成失败：' + errorMsg);
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

        // 切换 Tab 时清空预览
        watch(activeTab, () => {
            generatedReport.value = '';
        });

        // ==================== 返回 ====================
        return {
            // 状态
            form,
            weeklyForm,
            loading,
            generatedReport,
            activeTab,
            // 日期快捷选项
            dateShortcuts,
            // 日报方法
            submitRecord,
            generateDailyReport,
            // 周报方法
            generateWeeklyReport,
            // 通用方法
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
