// ==================== API Helper ====================
const API = {
    async get(url) {
        const response = await fetch(url);
        return response.json();
    },

    async post(url, data = {}) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    }
};

// ==================== Toast Notifications ====================
class ToastManager {
    constructor() {
        this.container = document.getElementById('toastContainer');
    }

    show(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">
                ${type === 'success' ?
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' :
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
                }
            </span>
            <span class="toast-message">${message}</span>
        `;
        this.container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

// ==================== App Class ====================
class App {
    constructor() {
        this.toast = new ToastManager();
        this.currentSection = 'dashboard';
        this.currentLogTab = 'runtime';
        this.videos = [];

        this.init();
    }

    async init() {
        this.bindEvents();
        this.createParticles();
        await this.loadConfig();
        await this.loadDouyinConfig();
        await this.loadVideos();
        await this.updateSchedulerStatus();
        await this.updateDouyinStatus();
        await this.loadLogStats();

        // 定时刷新状态
        setInterval(() => this.updateSchedulerStatus(), 60000);
        setInterval(() => this.loadLogStats(), 30000);
    }

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });

        // Quick actions
        document.getElementById('refreshVideos').addEventListener('click', () => this.loadVideos());
        document.getElementById('openFolder').addEventListener('click', () => this.openFolder());
        document.getElementById('startScheduler').addEventListener('click', () => this.startScheduler());
        document.getElementById('stopScheduler').addEventListener('click', () => this.stopScheduler());

        // Publish
        document.getElementById('publishBtn').addEventListener('click', () => this.openPublishModal());
        document.getElementById('closePublishModal').addEventListener('click', () => this.closePublishModal());
        document.getElementById('cancelPublish').addEventListener('click', () => this.closePublishModal());
        document.getElementById('confirmPublish').addEventListener('click', () => this.publishVideo());

        // Schedule form
        document.getElementById('scheduleForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSchedule();
        });

        // Scheduler controls
        document.getElementById('startSchedulerBtn').addEventListener('click', () => this.startScheduler());
        document.getElementById('stopSchedulerBtn').addEventListener('click', () => this.stopScheduler());

        // Settings
        document.getElementById('browseDir').addEventListener('click', () => this.browseDirectory());
        document.getElementById('saveCredentials').addEventListener('click', () => this.saveCredentials());
        document.getElementById('authorizeBtn').addEventListener('click', () => this.authorize());

        // Guide toggle
        document.getElementById('toggleGuide').addEventListener('click', () => this.toggleGuide());

        // Auth modal
        document.getElementById('closeAuthModal').addEventListener('click', () => this.closeAuthModal());
        document.getElementById('cancelAuth').addEventListener('click', () => this.closeAuthModal());
        document.getElementById('confirmAuth').addEventListener('click', () => this.confirmAuth());

        // Video search
        document.getElementById('videoSearch').addEventListener('input', (e) => this.searchVideos(e.target.value));
        document.getElementById('scanVideos').addEventListener('click', () => this.loadVideos());

        // Mobile menu
        document.getElementById('menuToggle').addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('active');
        });

        // Settings toggles
        document.getElementById('autoStart').addEventListener('change', (e) => {
            this.updateSetting('auto_start', e.target.checked);
        });

        document.getElementById('minimizeToTray').addEventListener('change', (e) => {
            this.updateSetting('minimize_to_tray', e.target.checked);
        });

        // Log tabs
        document.querySelectorAll('.log-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchLogTab(e.target.dataset.tab);
            });
        });

        // Log actions
        document.getElementById('refreshLogs').addEventListener('click', () => this.loadLogs());
        document.getElementById('clearAllLogs').addEventListener('click', () => this.clearAllLogs());
        document.getElementById('exportLogs').addEventListener('click', () => this.exportLogs());
        document.getElementById('logLevelFilter').addEventListener('change', () => this.loadLogs());

        // Video card links
        document.querySelectorAll('.card-link[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(e.target.dataset.section);
            });
        });
    }

    createParticles() {
        const container = document.getElementById('particles');
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.animationDelay = `${Math.random() * 6}s`;
            particle.style.animationDuration = `${4 + Math.random() * 4}s`;

            if (Math.random() > 0.5) {
                particle.style.background = 'var(--secondary)';
            }

            container.appendChild(particle);
        }
    }

    switchSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.section === section);
        });

        // Update sections
        document.querySelectorAll('.section').forEach(s => {
            s.classList.toggle('active', s.id === section);
        });

        // Update page title
        const titles = {
            dashboard: '仪表盘',
            videos: '视频管理',
            schedule: '定时任务',
            settings: '系统设置',
            logs: '日志管理'
        };
        document.getElementById('pageTitle').textContent = titles[section] || section;

        this.currentSection = section;

        // Load logs when switching to logs section
        if (section === 'logs') {
            this.loadLogs();
            this.loadLogStats();
        }

        // Close mobile menu
        document.querySelector('.sidebar').classList.remove('active');
    }

    async loadConfig() {
        try {
            const config = await API.get('/api/config');

            document.getElementById('videoDir').value = config.video_directory || '';
            document.getElementById('scheduleEnabled').checked = config.schedule.enabled;
            document.getElementById('scheduleTime').value = config.schedule.time || '17:00';
            document.getElementById('autoStart').checked = config.auto_start;
            document.getElementById('minimizeToTray').checked = config.minimize_to_tray;

            // Update day checkboxes
            document.querySelectorAll('input[name="days"]').forEach(cb => {
                cb.checked = config.schedule.days.includes(cb.value);
            });
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }

    async loadDouyinConfig() {
        try {
            const config = await API.get('/api/douyin/config');

            // 显示脱敏的 Client Key
            document.getElementById('clientKey').value = config.client_key || '';

            // 显示脱敏的 Client Secret
            const secretInput = document.getElementById('clientSecret');
            if (config.has_client_secret) {
                secretInput.value = config.client_secret;
                secretInput.dataset.hasValue = 'true';
                secretInput.placeholder = '已配置（输入新值可更新）';
            } else {
                secretInput.value = '';
                secretInput.dataset.hasValue = 'false';
                secretInput.placeholder = '输入 Client Secret';
            }
        } catch (error) {
            console.error('加载抖音配置失败:', error);
        }
    }

    async loadVideos() {
        try {
            const data = await API.get('/api/videos');
            this.videos = data.videos || [];

            this.renderVideoGrid();
            this.renderRecentVideos();
            document.getElementById('videoCount').textContent = this.videos.length;
        } catch (error) {
            console.error('加载视频失败:', error);
            this.toast.show('加载视频列表失败', 'error');
        }
    }

    renderVideoGrid() {
        const grid = document.getElementById('videoGrid');
        grid.innerHTML = this.videos.map(video => `
            <div class="video-card" data-path="${video.path}">
                <div class="video-thumbnail">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                </div>
                <div class="video-card-info">
                    <div class="video-card-name" title="${video.filename}">${video.filename}</div>
                    <div class="video-card-meta">
                        <span>${video.size_str}</span>
                        <span>${video.modified_time}</span>
                    </div>
                </div>
                <div class="video-card-actions">
                    <button class="btn btn-primary btn-sm" onclick="app.openPublishModal('${video.path}', '${video.filename}')">
                        发布
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderRecentVideos() {
        const container = document.getElementById('recentVideos');
        const recent = this.videos.slice(0, 5);

        container.innerHTML = recent.map(video => `
            <div class="video-item" onclick="app.openPublishModal('${video.path}', '${video.filename}')">
                <div class="video-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                </div>
                <div class="video-info">
                    <div class="video-name">${video.filename}</div>
                    <div class="video-meta">${video.size_str} · ${video.modified_time}</div>
                </div>
                <div class="video-action">
                    <button class="btn btn-secondary btn-sm">发布</button>
                </div>
            </div>
        `).join('');

        if (recent.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">暂无视频</div>';
        }
    }

    searchVideos(query) {
        const filtered = this.videos.filter(v =>
            v.filename.toLowerCase().includes(query.toLowerCase())
        );

        const grid = document.getElementById('videoGrid');
        grid.innerHTML = filtered.map(video => `
            <div class="video-card" data-path="${video.path}">
                <div class="video-thumbnail">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                </div>
                <div class="video-card-info">
                    <div class="video-card-name" title="${video.filename}">${video.filename}</div>
                    <div class="video-card-meta">
                        <span>${video.size_str}</span>
                        <span>${video.modified_time}</span>
                    </div>
                </div>
                <div class="video-card-actions">
                    <button class="btn btn-primary btn-sm" onclick="app.openPublishModal('${video.path}', '${video.filename}')">
                        发布
                    </button>
                </div>
            </div>
        `).join('');
    }

    openPublishModal(videoPath = '', filename = '') {
        document.getElementById('publishVideoPath').value = videoPath;
        document.getElementById('publishTitle').value = filename;
        document.getElementById('publishDesc').value = '';
        document.getElementById('publishModal').classList.add('active');
    }

    closePublishModal() {
        document.getElementById('publishModal').classList.remove('active');
    }

    async publishVideo() {
        const videoPath = document.getElementById('publishVideoPath').value;
        const title = document.getElementById('publishTitle').value;
        const description = document.getElementById('publishDesc').value;

        if (!videoPath) {
            this.toast.show('请先选择要发布的视频', 'error');
            return;
        }

        if (!title) {
            this.toast.show('请输入视频标题', 'error');
            return;
        }

        try {
            const result = await API.post('/api/publish', {
                video_path: videoPath,
                title: title,
                description: description
            });

            if (result.error) {
                this.toast.show(result.error, 'error');
            } else {
                this.toast.show('视频发布成功！');
                this.closePublishModal();
            }
        } catch (error) {
            this.toast.show('发布失败: ' + error.message, 'error');
        }
    }

    async saveSchedule() {
        const enabled = document.getElementById('scheduleEnabled').checked;
        const time = document.getElementById('scheduleTime').value;
        const days = Array.from(document.querySelectorAll('input[name="days"]:checked'))
            .map(cb => cb.value);

        try {
            await API.post('/api/config', {
                schedule: { enabled, days, time }
            });
            this.toast.show('定时配置已保存');
            await this.updateSchedulerStatus();
        } catch (error) {
            this.toast.show('保存失败', 'error');
        }
    }

    async startScheduler() {
        try {
            await API.post('/api/scheduler/start');
            this.toast.show('调度器已启动');
            await this.updateSchedulerStatus();
        } catch (error) {
            this.toast.show('启动调度器失败', 'error');
        }
    }

    async stopScheduler() {
        try {
            await API.post('/api/scheduler/stop');
            this.toast.show('调度器已停止');
            await this.updateSchedulerStatus();
        } catch (error) {
            this.toast.show('停止调度器失败', 'error');
        }
    }

    async updateSchedulerStatus() {
        try {
            const status = await API.get('/api/scheduler/status');

            document.getElementById('schedulerState').textContent = status.running ? '运行中' : '已停止';
            document.getElementById('jobCount').textContent = status.jobs_count || 0;
            document.getElementById('nextRun').textContent = status.next_run || '--';
            document.getElementById('nextPublish').textContent = status.next_run ? status.next_run.split(' ')[1] : '--:--';
            document.getElementById('schedulerStatus').textContent = status.running ? '运行中' : '停止';
        } catch (error) {
            console.error('获取调度状态失败:', error);
        }
    }

    async updateDouyinStatus() {
        try {
            const status = await API.get('/api/douyin/status');
            const badge = document.querySelector('.status-badge');
            const authInfo = document.getElementById('authStatusInfo');

            if (status.authenticated) {
                badge.className = 'status-badge authorized';
                badge.textContent = '已授权';
                document.getElementById('authStatus').textContent = '已连接';
                authInfo.className = 'auth-status-info authorized';
                authInfo.innerHTML = `
                    <div class="status-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                    </div>
                    <div class="status-text">
                        <strong>授权状态：已授权</strong>
                        <p>抖音账号已连接，可以正常发布视频</p>
                    </div>
                `;
            } else if (status.has_credentials) {
                badge.className = 'status-badge unauthorized';
                badge.textContent = '待授权';
                document.getElementById('authStatus').textContent = '待授权';
                authInfo.className = 'auth-status-info';
                authInfo.innerHTML = `
                    <div class="status-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="8" x2="12" y2="12"/>
                            <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                    </div>
                    <div class="status-text">
                        <strong>授权状态：待授权</strong>
                        <p>凭证已保存，请点击「授权登录」完成授权</p>
                    </div>
                `;
            } else {
                badge.className = 'status-badge unauthorized';
                badge.textContent = '未配置';
                document.getElementById('authStatus').textContent = '未连接';
                authInfo.className = 'auth-status-info';
                authInfo.innerHTML = `
                    <div class="status-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="8" x2="12" y2="12"/>
                            <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                    </div>
                    <div class="status-text">
                        <strong>授权状态：未配置</strong>
                        <p>请先填写 Client Key 和 Client Secret，然后点击「授权登录」</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('获取抖音状态失败:', error);
        }
    }

    toggleGuide() {
        const guide = document.getElementById('douyinGuide');
        const btn = document.getElementById('toggleGuide');
        const isVisible = guide.style.display !== 'none';

        guide.style.display = isVisible ? 'none' : 'block';
        btn.textContent = isVisible ? '查看配置指南' : '隐藏配置指南';
        btn.classList.toggle('active', !isVisible);
    }

    async browseDirectory() {
        const dir = prompt('请输入视频目录路径:');
        if (dir) {
            document.getElementById('videoDir').value = dir;
            await API.post('/api/config', { video_directory: dir });
            await this.loadVideos();
            this.toast.show('视频目录已更新');
        }
    }

    async openFolder() {
        try {
            const config = await API.get('/api/config');
            if (config.video_directory) {
                this.toast.show('文件夹路径: ' + config.video_directory);
            } else {
                this.toast.show('请先设置视频目录', 'error');
            }
        } catch (error) {
            this.toast.show('打开文件夹失败', 'error');
        }
    }

    async saveCredentials() {
        const clientKey = document.getElementById('clientKey').value;
        const clientSecret = document.getElementById('clientSecret').value;
        const secretInput = document.getElementById('clientSecret');
        const hasExistingSecret = secretInput.dataset.hasValue === 'true';

        // 验证输入
        if (!clientKey) {
            this.toast.show('请输入 Client Key', 'error');
            return;
        }

        // 如果没有已保存的密钥，且用户没有输入新密钥
        if (!hasExistingSecret && !clientSecret) {
            this.toast.show('请输入 Client Secret', 'error');
            return;
        }

        try {
            // 如果用户没有输入新的密钥，发送空字符串表示不更新
            const data = {
                client_key: clientKey,
                client_secret: hasExistingSecret && !clientSecret ? null : clientSecret
            };

            await API.post('/api/douyin/credentials', data);
            this.toast.show('凭证已保存（密文存储）');

            // 重新加载配置以显示脱敏后的密钥
            await this.loadDouyinConfig();
            await this.updateDouyinStatus();
        } catch (error) {
            this.toast.show('保存凭证失败', 'error');
        }
    }

    async authorize() {
        const clientKey = document.getElementById('clientKey').value;
        const clientSecret = document.getElementById('clientSecret').value;

        if (!clientKey || !clientSecret) {
            this.toast.show('请先填写并保存 Client Key 和 Client Secret', 'error');
            return;
        }

        try {
            const data = await API.get('/api/douyin/auth-url?redirect_uri=http://localhost:8080/callback');

            if (data.url) {
                window.open(data.url, '_blank');
                document.getElementById('authModal').classList.add('active');
            }
        } catch (error) {
            this.toast.show('获取授权链接失败', 'error');
        }
    }

    closeAuthModal() {
        document.getElementById('authModal').classList.remove('active');
    }

    async confirmAuth() {
        const code = document.getElementById('authCode').value;

        if (!code) {
            this.toast.show('请输入授权码', 'error');
            return;
        }

        try {
            const result = await API.post('/api/douyin/callback', { code });

            if (result.error) {
                this.toast.show(result.error, 'error');
            } else {
                this.toast.show('授权成功！');
                this.closeAuthModal();
                await this.updateDouyinStatus();
            }
        } catch (error) {
            this.toast.show('授权失败: ' + error.message, 'error');
        }
    }

    async updateSetting(key, value) {
        try {
            await API.post('/api/config', { [key]: value });
            this.toast.show('设置已更新');
        } catch (error) {
            this.toast.show('更新设置失败', 'error');
        }
    }

    // ==================== Log Management ====================

    switchLogTab(tab) {
        this.currentLogTab = tab;

        // Update tab buttons
        document.querySelectorAll('.log-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });

        // Update content
        document.querySelectorAll('.log-content').forEach(c => {
            c.classList.toggle('active', c.id === `${tab}Logs`);
        });

        // Load logs for the selected tab
        this.loadLogs();
    }

    async loadLogStats() {
        try {
            const stats = await API.get('/api/logs/stats');
            document.getElementById('runtimeLogCount').textContent = stats.runtime_lines || 0;
            document.getElementById('operationLogCount').textContent = stats.operation_count || 0;
            document.getElementById('errorLogCount').textContent = stats.error_lines || 0;
        } catch (error) {
            console.error('加载日志统计失败:', error);
        }
    }

    async loadLogs() {
        try {
            if (this.currentLogTab === 'runtime') {
                await this.loadRuntimeLogs();
            } else if (this.currentLogTab === 'operations') {
                await this.loadOperationLogs();
            } else if (this.currentLogTab === 'errors') {
                await this.loadErrorLogs();
            }
        } catch (error) {
            console.error('加载日志失败:', error);
        }
    }

    async loadRuntimeLogs() {
        const level = document.getElementById('logLevelFilter').value;
        const data = await API.get(`/api/logs/runtime?lines=100&level=${level}`);
        const logs = data.logs || [];

        const container = document.getElementById('runtimeLogList');
        if (logs.length === 0) {
            container.innerHTML = '<div class="log-empty">暂无运行日志</div>';
            return;
        }

        container.innerHTML = logs.map(log => `
            <div class="log-entry">
                <span class="log-timestamp">${log.timestamp}</span>
                <span class="log-level ${(log.level || 'info').toLowerCase()}">${log.level || 'INFO'}</span>
                <span class="log-message">${log.message}</span>
            </div>
        `).join('');

        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    async loadOperationLogs() {
        const data = await API.get('/api/logs/operations?limit=100');
        const logs = data.logs || [];

        const container = document.getElementById('operationLogList');
        if (logs.length === 0) {
            container.innerHTML = '<div class="log-empty">暂无操作记录</div>';
            return;
        }

        container.innerHTML = logs.reverse().map(log => `
            <div class="log-operation">
                <div class="log-operation-icon ${log.status === 'success' ? 'success' : 'failed'}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${log.status === 'success'
                            ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'
                            : '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'
                        }
                    </svg>
                </div>
                <div class="log-operation-info">
                    <div class="log-operation-action">${log.action}</div>
                    <div class="log-operation-details">${log.details || ''}</div>
                </div>
                <div class="log-operation-time">${log.timestamp}</div>
            </div>
        `).join('');

        // Scroll to top (newest first)
        container.scrollTop = 0;
    }

    async loadErrorLogs() {
        const data = await API.get('/api/logs/errors?lines=50');
        const logs = data.logs || [];

        const container = document.getElementById('errorLogList');
        if (logs.length === 0) {
            container.innerHTML = '<div class="log-empty">暂无错误日志</div>';
            return;
        }

        container.innerHTML = logs.map(log => `
            <div class="log-entry">
                <span class="log-timestamp">${log.timestamp}</span>
                <span class="log-level error">ERROR</span>
                <span class="log-message">${log.message}</span>
            </div>
        `).join('');

        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    async clearAllLogs() {
        if (!confirm('确定要清除所有日志吗？此操作不可撤销。')) {
            return;
        }

        try {
            await API.post('/api/logs/clear', { type: 'all' });
            this.toast.show('所有日志已清除');
            await this.loadLogs();
            await this.loadLogStats();
        } catch (error) {
            this.toast.show('清除日志失败', 'error');
        }
    }

    async exportLogs() {
        try {
            let content = '';

            if (this.currentLogTab === 'runtime') {
                const data = await API.get('/api/logs/runtime?lines=1000');
                content = (data.logs || []).map(l => `${l.timestamp} [${l.level}] ${l.message}`).join('\n');
            } else if (this.currentLogTab === 'operations') {
                const data = await API.get('/api/logs/operations?limit=1000');
                content = (data.logs || []).map(l => `${l.timestamp} ${l.action} ${l.details} [${l.status}]`).join('\n');
            } else if (this.currentLogTab === 'errors') {
                const data = await API.get('/api/logs/errors?lines=1000');
                content = (data.logs || []).map(l => `${l.timestamp} ${l.message}`).join('\n');
            }

            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.currentLogTab}_logs_${new Date().toISOString().slice(0, 10)}.txt`;
            a.click();
            URL.revokeObjectURL(url);

            this.toast.show('日志已导出');
        } catch (error) {
            this.toast.show('导出日志失败', 'error');
        }
    }
}

// ==================== Initialize App ====================
const app = new App();
