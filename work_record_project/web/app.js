const { createApp, ref, reactive } = Vue;
const { ElMessage, ElLoading } = ElementPlus;

const app = createApp({
    setup() {
        // 状态定义
        const loading = ref(false);
        const generatedReport = ref('');
        const activeTab = ref('daily'); // daily | weekly

        // 表单数据
        const form = reactive({
            record_date: new Date().toISOString().split('T')[0],
            project: '',
            tomorrow: '',
            product: '',
            others: '',
            risks: ''
        });

        // API 基础地址
        const API_BASE_URL = 'http://localhost:8000/api';

        // 提交工作记录
        const submitRecord = async () => {
            if (!form.project || !form.tomorrow) {
                ElMessage.warning('请填写必填项：项目工作和明日计划');
                return;
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
        const generateReport = async () => {
            // 先保存记录
            const saved = await submitRecord();
            if (!saved) return;

            try {
                const loadingInstance = ElLoading.service({
                    text: '正在调用大模型生成日报，请稍候...',
                    background: 'rgba(0, 0, 0, 0.7)'
                });

                const response = await axios.post(
                    `${API_BASE_URL}/records/daily/generate?record_date=${form.record_date}`
                );

                generatedReport.value = response.data;
                ElMessage.success('日报生成成功！');
                loadingInstance.close();
            } catch (error) {
                console.error(error);
                ElMessage.error('生成失败：' + (error.response?.data?.detail || error.message));
                if (window.loadingInstance) window.loadingInstance.close();
            }
        };

        // 复制日报内容
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

        return {
            form,
            loading,
            generatedReport,
            activeTab,
            submitRecord,
            generateReport,
            copyReport,
            renderMarkdown
        };
    }
});

app.use(ElementPlus);
app.mount('#app');
