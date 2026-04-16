<template>
  <div class="app-shell">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-icon">🌾</span>
        <span class="logo-text">FarmerClaw</span>
        <span class="logo-sub">三农AI运营平台</span>
      </div>

      <nav class="nav">
        <router-link to="/home" class="nav-item" active-class="active">
          <span class="nav-icon">🏠</span>
          <span>首页</span>
        </router-link>

        <div class="nav-section-label">核心功能</div>

        <router-link to="/content-pack" class="nav-item nav-item-main" active-class="active">
          <span class="nav-icon">📦</span>
          <span>选题 + 口播稿</span>
          <span class="nav-tag">HOT</span>
        </router-link>
        <router-link to="/listing" class="nav-item nav-item-main" active-class="active">
          <span class="nav-icon">🔴</span>
          <span>直播话术积木</span>
        </router-link>
        <router-link to="/reply" class="nav-item nav-item-main" active-class="active">
          <span class="nav-icon">�</span>
          <span>差评/售后回复</span>
        </router-link>
        <router-link to="/pain-point" class="nav-item nav-item-main" active-class="active">
          <span class="nav-icon">🔍</span>
          <span>痛点挖掘 + 卖点</span>
        </router-link>

        <div class="nav-section-label">运营工具</div>

        <router-link to="/dashboard" class="nav-item" active-class="active">
          <span class="nav-icon">📊</span>
          <span>数据看板</span>
        </router-link>
        <router-link to="/history" class="nav-item" active-class="active">
          <span class="nav-icon">📋</span>
          <span>历史记录</span>
        </router-link>
        <router-link to="/samples" class="nav-item" active-class="active">
          <span class="nav-icon">�️</span>
          <span>样本库</span>
        </router-link>

        <div class="nav-section-label">即将上线</div>
        <div class="nav-item nav-item-disabled">
          <span class="nav-icon">�</span>
          <span>投放优化</span>
          <span class="nav-tag-soon">开发中</span>
        </div>
        <div class="nav-item nav-item-disabled">
          <span class="nav-icon">⚡</span>
          <span>全流程一键生成</span>
          <span class="nav-tag-soon">开发中</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <!-- 已登录：用户信息 -->
        <div v-if="auth.isLoggedIn" class="user-info">
          <div class="user-row">
            <div class="user-name">{{ auth.user?.name || auth.user?.email }}</div>
            <span :class="['tier-badge', `tier-${auth.tier}`]">{{ auth.tierLabel }}</span>
          </div>
          <!-- 用量进度条 -->
          <div class="usage-bar" v-if="auth.user?.limits">
            <div class="usage-row">
              <span>痛点分析</span>
              <span>{{ auth.user.pain_point_count }}/{{ auth.user.limits.pain_point }}</span>
            </div>
            <div class="usage-track">
              <div class="usage-fill" :style="{ width: usagePct('pain_point') + '%' }"></div>
            </div>
          </div>
          <router-link v-if="auth.tier === 'free'" to="/pricing" class="upgrade-cta">⬆️ 升级解锁更多</router-link>
          <button class="logout-btn" @click="logout">退出登录</button>
        </div>
        <!-- 未登录 -->
        <router-link v-else to="/login" class="login-link">🔑 登录 / 注册</router-link>
        <div class="version-badge">MVP v1.0</div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth.js'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => { auth.fetchMe() })

const logout = () => {
  auth.logout()
  router.push('/login')
}

const usagePct = (field) => {
  const used = auth.user?.[`${field}_count`] ?? 0
  const limit = auth.user?.limits?.[field] ?? 1
  return Math.min(100, Math.round((used / limit) * 100))
}
</script>

<style>
/* ── 全局变量 ── */
:root {
  --green-primary: #22c55e;
  --green-dark: #16a34a;
  --green-light: #bbf7d0;
  --green-bg: #f0fdf4;
  --orange-primary: #f97316;
  --orange-light: #fed7aa;
  --sidebar-width: 220px;
  --border: #e5e7eb;
  --text: #111827;
  --text-muted: #6b7280;
  --card-bg: #fff;
  --shadow: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,.08), 0 2px 4px -1px rgba(0,0,0,.05);
  --radius: 12px;
  --radius-sm: 8px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f8fafc;
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
}

/* ── 布局 ── */
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-width);
  background: linear-gradient(180deg, #14532d 0%, #166534 40%, #15803d 100%);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
}

.logo {
  padding: 24px 20px 20px;
  border-bottom: 1px solid rgba(255,255,255,.12);
}
.logo-icon { font-size: 28px; display: block; }
.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: .5px;
  display: block;
  margin-top: 4px;
}
.logo-sub {
  font-size: 11px;
  color: rgba(255,255,255,.6);
  display: block;
  margin-top: 2px;
}

.nav { flex: 1; padding: 16px 12px; display: flex; flex-direction: column; gap: 4px; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: rgba(255,255,255,.75);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all .15s ease;
}
.nav-item:hover { background: rgba(255,255,255,.12); color: #fff; }
.nav-item.active {
  background: rgba(255,255,255,.15);
  color: #fff;
}
.nav-item-main {
  background: rgba(255,255,255,.1);
  border: 1px solid rgba(255,255,255,.2);
  margin-bottom: 4px;
}
.nav-item-main.active {
  background: rgba(255,255,255,.25);
}
.nav-divider {
  font-size: 10px;
  font-weight: 700;
  color: rgba(255,255,255,.4);
  text-transform: uppercase;
  letter-spacing: .08em;
  padding: 12px 12px 4px;
}
.nav-section-label {
  font-size: 10px;
  font-weight: 700;
  color: rgba(255,255,255,.45);
  text-transform: uppercase;
  letter-spacing: .08em;
  padding: 14px 12px 6px;
}
.nav-tag {
  margin-left: auto;
  font-size: 9px;
  font-weight: 800;
  background: #f59e0b;
  color: #fff;
  border-radius: 4px;
  padding: 1px 5px;
  letter-spacing: .04em;
}
.nav-tag-soon {
  margin-left: auto;
  font-size: 9px;
  font-weight: 600;
  background: rgba(255,255,255,.15);
  color: rgba(255,255,255,.5);
  border-radius: 4px;
  padding: 1px 5px;
}
.nav-item-disabled {
  opacity: .5;
  cursor: not-allowed;
  pointer-events: none;
}
.nav-icon { font-size: 18px; width: 24px; text-align: center; }

.sidebar-footer {
  padding: 16px 20px 24px;
  border-top: 1px solid rgba(255,255,255,.1);
}
.version-badge {
  display: inline-block;
  background: rgba(255,255,255,.15);
  color: rgba(255,255,255,.8);
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 99px;
  margin-top: 6px;
}
.user-info { margin-bottom: 8px; display: flex; flex-direction: column; gap: 6px; }
.user-row { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
.user-name { font-size: 12px; font-weight: 600; color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tier-badge { font-size: 9px; font-weight: 700; padding: 1px 6px; border-radius: 4px; flex-shrink: 0; }
.tier-free { background: rgba(255,255,255,.2); color: rgba(255,255,255,.8); }
.tier-basic { background: #bfdbfe; color: #1e40af; }
.tier-pro { background: #bbf7d0; color: #15803d; }
.tier-enterprise { background: #fde68a; color: #92400e; }
.usage-bar { }
.usage-row { display: flex; justify-content: space-between; font-size: 10px; color: rgba(255,255,255,.6); margin-bottom: 3px; }
.usage-track { height: 4px; background: rgba(255,255,255,.15); border-radius: 99px; overflow: hidden; }
.usage-fill { height: 100%; background: var(--green-primary); border-radius: 99px; transition: width .4s ease; }
.upgrade-cta {
  display: block; text-align: center; font-size: 11px; font-weight: 700;
  color: #fef08a; text-decoration: none; background: rgba(255,255,255,.1);
  padding: 5px; border-radius: 5px; border: 1px solid rgba(255,255,255,.2);
}
.upgrade-cta:hover { background: rgba(255,255,255,.2); }
.logout-btn {
  font-size: 11px; padding: 4px 10px;
  background: rgba(255,255,255,.1); color: rgba(255,255,255,.7);
  border: 1px solid rgba(255,255,255,.15); border-radius: 5px; cursor: pointer; width: 100%;
}
.logout-btn:hover { background: rgba(255,255,255,.2); }
.login-link {
  display: block; font-size: 12px; font-weight: 600; color: #fff;
  text-decoration: none; margin-bottom: 8px;
  background: var(--green-primary); padding: 7px 10px; border-radius: 7px; text-align: center;
}
.login-link:hover { background: var(--green-dark); }

.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f8fafc;
}

/* ── 通用卡片 ── */
.card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
  border: 1px solid var(--border);
}

.page-header {
  padding: 28px 32px 0;
  margin-bottom: 24px;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
}
.page-desc { color: var(--text-muted); margin-top: 4px; font-size: 14px; }

/* ── 按钮 ── */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 600;
  cursor: pointer; border: none; transition: all .15s ease; white-space: nowrap;
}
.btn-primary {
  background: var(--green-primary); color: #fff;
}
.btn-primary:hover:not(:disabled) { background: var(--green-dark); transform: translateY(-1px); box-shadow: var(--shadow-md); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }

.btn-secondary {
  background: #f3f4f6; color: var(--text); border: 1px solid var(--border);
}
.btn-secondary:hover { background: #e5e7eb; }

.btn-orange {
  background: var(--orange-primary); color: #fff;
}
.btn-orange:hover:not(:disabled) { background: #ea6d10; }
.btn-orange:disabled { opacity: .6; cursor: not-allowed; }

/* ── 表单 ── */
.form-group { margin-bottom: 16px; }
.form-label {
  display: block; font-size: 13px; font-weight: 600;
  color: var(--text); margin-bottom: 6px;
}
.form-label .required { color: #ef4444; margin-left: 2px; }
.form-input, .form-select, .form-textarea {
  width: 100%; padding: 10px 12px; border: 1.5px solid var(--border);
  border-radius: 8px; font-size: 14px; color: var(--text);
  background: #fff; transition: border-color .15s ease; outline: none;
  font-family: inherit;
}
.form-input:focus, .form-select:focus, .form-textarea:focus {
  border-color: var(--green-primary); box-shadow: 0 0 0 3px rgba(34,197,94,.12);
}
.form-textarea { resize: vertical; min-height: 80px; }

/* ── 标签/徽章 ── */
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 99px;
  font-size: 11px; font-weight: 600;
}
.badge-green { background: var(--green-light); color: var(--green-dark); }
.badge-orange { background: var(--orange-light); color: #c2410c; }
.badge-red { background: #fee2e2; color: #dc2626; }
.badge-gray { background: #f3f4f6; color: var(--text-muted); }

/* ── loading ── */
.loading-spinner {
  display: inline-block; width: 20px; height: 20px;
  border: 2px solid rgba(255,255,255,.4); border-top-color: #fff;
  border-radius: 50%; animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 分割线 ── */
.divider { height: 1px; background: var(--border); margin: 20px 0; }

/* ── 空状态 ── */
.empty-state {
  text-align: center; padding: 48px 24px; color: var(--text-muted);
}
.empty-state .empty-icon { font-size: 48px; margin-bottom: 12px; display: block; }

/* ── 响应式 ── */

/* 平板（侧边栏收窄） */
@media (max-width: 900px) {
  .sidebar { width: 56px; }
  .logo-text, .logo-sub, .nav-divider,
  .nav-item span:last-child, .sidebar-footer { display: none; }
  .logo-mark { font-size: 22px; }
  .nav-icon { font-size: 20px; width: 28px; }
  .nav-item { justify-content: center; padding: 10px 0; }
}

/* 手机（侧边栏底部固定） */
@media (max-width: 600px) {
  .app-layout { flex-direction: column; }

  .sidebar {
    width: 100%; height: auto;
    flex-direction: row; align-items: center;
    position: fixed; bottom: 0; left: 0; right: 0;
    z-index: 100; padding: 0;
    border-right: none; border-top: 1px solid rgba(255,255,255,.15);
  }
  .sidebar-logo { display: none; }
  .sidebar-nav {
    display: flex; flex-direction: row; flex: 1;
    overflow-x: auto; padding: 0 4px; gap: 0;
  }
  .nav-item { flex-direction: column; gap: 2px; font-size: 9px; padding: 8px 10px; }
  .nav-item span:last-child { display: block; font-size: 9px; }
  .nav-icon { font-size: 18px; width: auto; }
  .nav-divider { display: none; }
  .sidebar-footer { display: none; }

  .main-content { padding-bottom: 64px; }
  .page-header { padding: 16px 16px 0; }
  .page-body { padding: 0 16px 16px !important; }

  /* 所有双栏布局降为单栏 */
  .layout,
  .main-layout,
  .charts-row,
  .form-row,
  .form-row3,
  .pb-row,
  .metrics-grid { grid-template-columns: 1fr !important; }

  .form-col, .result-col, .input-col { max-width: 100%; }
}
</style>
