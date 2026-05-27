// ==================== API Helper ====================
const API = {
    async get(url) {
        const response = await fetch(url);
        if (!response.ok) {
            const err = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(err.error || `请求失败: ${response.status}`);
        }
        return response.json();
    },

    async post(url, data = {}) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(err.error || `请求失败: ${response.status}`);
        }
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
        this.publishedRecords = {};

        this.init();
    }

    _escapeAttr(str) {
        return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    _escapeHtml(str) {
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    async init() {
        this.bindEvents();
        this.createParticles();
        await this.loadConfig();
        await this.loadDouyinConfig();
        await this.loadAccounts();
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

        // Video grid (event delegation)
        document.getElementById('videoGrid').addEventListener('click', (e) => {
            const btn = e.target.closest('.publish-btn');
            if (btn) {
                const card = btn.closest('.video-card');
                if (card) this.openPublishModal(card.dataset.path, card.dataset.filename);
                return;
            }
            const thumb = e.target.closest('.video-thumbnail');
            if (thumb) {
                const card = thumb.closest('.video-card');
                if (card) this.openPreviewModal(card.dataset.path, card.dataset.filename, card.dataset.size);
            }
        });

        // Recent videos (event delegation)
        document.getElementById('recentVideos').addEventListener('click', (e) => {
            const item = e.target.closest('.video-item');
            if (item && item.dataset.path) {
                this.openPublishModal(item.dataset.path, item.dataset.filename);
            }
        });

        // Publish
        document.getElementById('publishBtn').addEventListener('click', () => this.openPublishModal());
        document.getElementById('closePublishModal').addEventListener('click', () => this.closePublishModal());
        document.getElementById('cancelPublish').addEventListener('click', () => this.closePublishModal());
        document.getElementById('confirmPublish').addEventListener('click', () => this.publishVideo());

        // Preview modal
        document.getElementById('closePreviewModal').addEventListener('click', () => this.closePreviewModal());
        document.getElementById('previewPublishBtn').addEventListener('click', () => {
            const video = document.getElementById('previewVideo');
            const path = video.dataset.path;
            const filename = document.getElementById('previewFilename').textContent;
            this.closePreviewModal();
            this.openPublishModal(path, filename);
        });

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

        // Scan login
        document.getElementById('checkLoginStatus').addEventListener('click', () => this.updateDouyinStatus());

        // Account management
        document.getElementById('addAccountBtn').addEventListener('click', () => this.addAccount());

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
            await API.get('/api/douyin/config');
        } catch (error) {
            console.error('加载抖音配置失败:', error);
        }
    }

    async loadVideos() {
        try {
            const [videoData, publishedData] = await Promise.all([
                API.get('/api/videos'),
                API.get('/api/published').catch(() => ({ records: {} }))
            ]);
            this.videos = videoData.videos || [];
            this.publishedRecords = publishedData.records || {};

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
        grid.innerHTML = this.videos.map(video => {
            const pubBadge = this.publishedRecords && this.publishedRecords[video.filename]
                ? '<span class="published-badge">已发布</span>' : '';
            const meta = video.meta || {};
            const displayName = meta.title || video.filename;
            const coverHtml = meta.cover
                ? `<img class="video-card-cover" src="/api/video/cover?path=${encodeURIComponent(meta.cover)}" alt="" loading="lazy">`
                : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
            const coverClass = meta.cover ? 'with-cover' : '';
            return `
            <div class="video-card" data-path="${this._escapeAttr(video.path)}" data-filename="${this._escapeAttr(video.filename)}" data-size="${this._escapeAttr(video.size_str)}">
                <div class="video-thumbnail ${coverClass}">
                    ${coverHtml}
                </div>
                <div class="video-card-info">
                    <div class="video-card-name" title="${this._escapeAttr(video.filename)}">${this._escapeHtml(displayName)}${pubBadge}</div>
                    <div class="video-card-meta">
                        <span>${video.size_str}</span>
                        <span>${video.modified_time}</span>
                    </div>
                </div>
                <div class="video-card-actions">
                    <button class="btn btn-primary btn-sm publish-btn">发布</button>
                </div>
            </div>`;
        }).join('');
    }

    renderRecentVideos() {
        const container = document.getElementById('recentVideos');
        const recent = this.videos.slice(0, 5);

        container.innerHTML = recent.map(video => {
            const meta = video.meta || {};
            const displayName = meta.title || video.filename;
            return `
            <div class="video-item" data-path="${this._escapeAttr(video.path)}" data-filename="${this._escapeAttr(video.filename)}">
                <div class="video-icon">
                    ${meta.cover
                        ? `<img src="/api/video/cover?path=${encodeURIComponent(meta.cover)}" style="width:36px;height:36px;border-radius:6px;object-fit:cover;" alt="">`
                        : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>`
                    }
                </div>
                <div class="video-info">
                    <div class="video-name">${this._escapeHtml(displayName)}</div>
                    <div class="video-meta">${video.size_str} · ${video.modified_time}</div>
                </div>
                <div class="video-action">
                    <button class="btn btn-secondary btn-sm">发布</button>
                </div>
            </div>`;
        }).join('');

        if (recent.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">暂无视频</div>';
        }
    }

    searchVideos(query) {
        const filtered = this.videos.filter(v =>
            v.filename.toLowerCase().includes(query.toLowerCase())
        );

        const grid = document.getElementById('videoGrid');
        grid.innerHTML = filtered.map(video => {
            const pubBadge = this.publishedRecords && this.publishedRecords[video.filename]
                ? '<span class="published-badge">已发布</span>' : '';
            const meta = video.meta || {};
            const displayName = meta.title || video.filename;
            const coverHtml = meta.cover
                ? `<img class="video-card-cover" src="/api/video/cover?path=${encodeURIComponent(meta.cover)}" alt="" loading="lazy">`
                : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
            const coverClass = meta.cover ? 'with-cover' : '';
            return `
            <div class="video-card" data-path="${this._escapeAttr(video.path)}" data-filename="${this._escapeAttr(video.filename)}" data-size="${this._escapeAttr(video.size_str)}">
                <div class="video-thumbnail ${coverClass}">
                    ${coverHtml}
                </div>
                <div class="video-card-info">
                    <div class="video-card-name" title="${this._escapeAttr(video.filename)}">${this._escapeHtml(displayName)}${pubBadge}</div>
                    <div class="video-card-meta">
                        <span>${video.size_str}</span>
                        <span>${video.modified_time}</span>
                    </div>
                </div>
                <div class="video-card-actions">
                    <button class="btn btn-primary btn-sm publish-btn">发布</button>
                </div>
            </div>`;
        }).join('');
    }

    openPublishModal(videoPath = '', filename = '') {
        document.getElementById('publishVideoPath').value = videoPath;
        document.getElementById('publishVideoFilename').value = filename;

        // 从元数据预填字段
        const video = this.videos.find(v => v.filename === filename);
        const meta = video ? video.meta : null;

        document.getElementById('publishTitle').value = (meta && meta.title) || filename;
        document.getElementById('publishDesc').value = (meta && meta.description) || '';
        document.getElementById('publishTags').value = (meta && meta.tags) || '';

        // 封面预览
        const coverPreview = document.getElementById('publishCoverPreview');
        const coverImg = document.getElementById('publishCoverImg');
        if (meta && meta.cover) {
            coverImg.src = `/api/video/cover?path=${encodeURIComponent(meta.cover)}`;
            coverPreview.style.display = 'block';
        } else {
            coverPreview.style.display = 'none';
        }

        document.getElementById('publishModal').classList.add('active');
    }

    closePublishModal() {
        document.getElementById('publishModal').classList.remove('active');
    }

    openPreviewModal(videoPath, filename, fileSize) {
        const video = document.getElementById('previewVideo');
        const container = video.parentElement;

        // 移除旧的错误提示
        const oldErr = container.querySelector('.preview-error');
        if (oldErr) oldErr.remove();

        // 添加加载指示器
        video.style.display = 'none';
        let loader = container.querySelector('.preview-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.className = 'preview-loader';
            loader.textContent = '加载中...';
            loader.style.cssText = 'color:var(--text-muted);text-align:center;padding:60px 0;font-size:14px;';
            container.appendChild(loader);
        }
        loader.style.display = 'block';

        video.src = `/api/video/preview?path=${encodeURIComponent(videoPath)}`;
        video.dataset.path = videoPath;

        video.onloadeddata = () => {
            loader.style.display = 'none';
            video.style.display = 'block';
        };

        video.onerror = () => {
            loader.style.display = 'none';
            video.style.display = 'none';
            const err = document.createElement('div');
            err.className = 'preview-error';
            err.textContent = '视频加载失败，请检查文件格式或路径';
            err.style.cssText = 'color:#F44336;text-align:center;padding:60px 0;font-size:14px;';
            container.appendChild(err);
        };

        document.getElementById('previewFilename').textContent = filename || '';
        document.getElementById('previewFilesize').textContent = fileSize || '';
        document.getElementById('previewModal').classList.add('active');
    }

    closePreviewModal() {
        const video = document.getElementById('previewVideo');
        const container = video.parentElement;
        video.pause();
        video.removeAttribute('src');
        video.load();
        video.onloadeddata = null;
        video.onerror = null;
        // 清理加载/错误提示
        const loader = container.querySelector('.preview-loader');
        if (loader) loader.remove();
        const err = container.querySelector('.preview-error');
        if (err) err.remove();
        video.style.display = 'block';
        document.getElementById('previewModal').classList.remove('active');
    }

    // ==================== Account Management ====================

    async loadAccounts() {
        try {
            const data = await API.get('/api/accounts');
            this.accounts = data.accounts || [];
            this.activeAccountId = data.active_account;
            this.renderAccountList();
            this.renderCurrentAccount();
        } catch (error) {
            console.error('加载账号列表失败:', error);
        }
    }

    renderCurrentAccount() {
        const active = this.accounts.find(a => a.account_id === this.activeAccountId);
        const nameEl = document.getElementById('currentAccountName');
        const statusEl = document.getElementById('currentAccountStatus');

        if (active) {
            nameEl.textContent = active.nickname;
            statusEl.textContent = '当前活跃';
            statusEl.className = 'account-status authenticated';
        } else {
            nameEl.textContent = '默认账号';
            statusEl.textContent = '未选择';
            statusEl.className = 'account-status';
        }
    }

    renderAccountList() {
        const container = document.getElementById('accountList');
        if (!this.accounts || this.accounts.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 12px; font-size: 13px;">暂无账号，请点击添加</div>';
            return;
        }

        container.innerHTML = this.accounts.map(acc => `
            <div class="account-item ${acc.account_id === this.activeAccountId ? 'active' : ''}" data-id="${acc.account_id}">
                <div class="account-item-info">
                    <div class="account-item-avatar">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                            <circle cx="12" cy="7" r="4"/>
                        </svg>
                    </div>
                    <div>
                        <div class="account-item-name">${this._escapeHtml(acc.nickname)}</div>
                        <div class="account-item-meta">最后使用: ${acc.last_used || '--'}</div>
                    </div>
                </div>
                <div class="account-item-actions">
                    ${acc.account_id !== this.activeAccountId ?
                        `<button class="btn btn-secondary btn-sm switch-account-btn" data-id="${acc.account_id}">切换</button>` :
                        '<span class="published-badge">当前</span>'
                    }
                    <button class="btn btn-danger btn-sm remove-account-btn" data-id="${acc.account_id}">删除</button>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('.switch-account-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.switchAccount(btn.dataset.id);
            });
        });

        container.querySelectorAll('.remove-account-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeAccount(btn.dataset.id);
            });
        });
    }

    async addAccount() {
        try {
            const result = await API.post('/api/accounts/create-and-login');
            if (result.error) {
                this.toast.show(result.error, 'error');
                return;
            }
            this.toast.show('浏览器已打开，请扫码登录');
            this._startCreateLoginPolling();
        } catch (error) {
            this.toast.show('启动登录失败: ' + error.message, 'error');
        }
    }

    _startCreateLoginPolling() {
        const pollInterval = setInterval(async () => {
            try {
                const status = await API.get('/api/accounts/create-and-login/status');
                if (status.result === 'success') {
                    clearInterval(pollInterval);
                    const name = status.account ? status.account.nickname : '新账号';
                    this.toast.show(`登录成功！已添加账号: ${name}`);
                    await this.loadAccounts();
                    await this.updateDouyinStatus();
                } else if (status.result === 'failed') {
                    clearInterval(pollInterval);
                    this.toast.show('登录失败或已取消，未添加账号', 'error');
                }
            } catch (error) {
                clearInterval(pollInterval);
                console.error('轮询登录状态失败:', error);
            }
        }, 3000);

        setTimeout(() => clearInterval(pollInterval), 180000);
    }

    async switchAccount(accountId) {
        try {
            const result = await API.post('/api/accounts/switch', { account_id: accountId });
            if (result.success) {
                this.toast.show(`已切换到: ${result.account.nickname}`);
                await this.loadAccounts();
                await this.updateDouyinStatus();
            }
        } catch (error) {
            this.toast.show('切换账号失败', 'error');
        }
    }

    async removeAccount(accountId) {
        if (!confirm('确定要删除此账号吗？相关的登录信息将被清除。')) return;
        try {
            const result = await API.post('/api/accounts/remove', { account_id: accountId });
            if (result.success) {
                this.toast.show('账号已删除');
                await this.loadAccounts();
            }
        } catch (error) {
            this.toast.show('删除账号失败', 'error');
        }
    }

    async publishVideo() {
        const videoPath = document.getElementById('publishVideoPath').value;
        const filename = document.getElementById('publishVideoFilename').value;
        const title = document.getElementById('publishTitle').value;
        const description = document.getElementById('publishDesc').value;
        const tags = document.getElementById('publishTags').value;

        if (!videoPath) {
            this.toast.show('请先选择要发布的视频', 'error');
            return;
        }

        const btn = document.getElementById('confirmPublish');
        const origText = btn.textContent;
        btn.disabled = true;
        btn.textContent = '发布中...';

        try {
            const result = await API.post('/api/publish', {
                video_path: videoPath,
                title: title || filename,
                description: description,
                tags: tags
            });

            this.toast.show('视频发布成功！');
            this.closePublishModal();
            await this.loadVideos();
        } catch (error) {
            this.toast.show('发布失败: ' + error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = origText;
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
                badge.textContent = '已登录';
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
                        <strong>登录状态：已登录</strong>
                        <p>抖音账号已连接，可以正常发布视频</p>
                    </div>
                `;
            } else if (status.login_in_progress) {
                badge.className = 'status-badge';
                badge.textContent = '登录中';
                document.getElementById('authStatus').textContent = '登录中';
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
                        <strong>登录状态：等待扫码</strong>
                        <p>浏览器已打开，请使用抖音 APP 扫描二维码</p>
                    </div>
                `;
            } else {
                badge.className = 'status-badge unauthorized';
                badge.textContent = '未登录';
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
                        <strong>登录状态：未登录</strong>
                        <p>请点击「扫码登录」按钮登录抖音账号</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('获取抖音状态失败:', error);
        }
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
