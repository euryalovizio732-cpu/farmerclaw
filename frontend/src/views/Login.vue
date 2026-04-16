<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="brand">
        <span class="brand-icon">🌾</span>
        <h1 class="brand-name">FarmerClaw</h1>
        <p class="brand-sub">三农电商 AI 运营平台</p>
      </div>

      <!-- Tab -->
      <div class="tabs">
        <button :class="['tab', { active: mode === 'login' }]" @click="mode = 'login'">登录</button>
        <button :class="['tab', { active: mode === 'register' }]" @click="mode = 'register'">免费注册</button>
      </div>

      <!-- 登录表单 -->
      <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="form">
        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input v-model="email" type="email" class="form-input" placeholder="your@email.com" required />
        </div>
        <div class="form-group">
          <label class="form-label">密码</label>
          <input v-model="password" type="password" class="form-input" placeholder="请输入密码" required />
        </div>
        <div class="error-msg" v-if="error">{{ error }}</div>
        <button type="submit" class="btn btn-primary w-full" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          <span>{{ loading ? '登录中...' : '登录' }}</span>
        </button>
      </form>

      <!-- 注册表单 -->
      <form v-else @submit.prevent="handleRegister" class="form">
        <div class="form-group">
          <label class="form-label">姓名/昵称</label>
          <input v-model="name" type="text" class="form-input" placeholder="您的称呼" />
        </div>
        <div class="form-group">
          <label class="form-label">邮箱 <span class="required">*</span></label>
          <input v-model="email" type="email" class="form-input" placeholder="your@email.com" required />
        </div>
        <div class="form-group">
          <label class="form-label">密码 <span class="required">*</span>（至少6位）</label>
          <input v-model="password" type="password" class="form-input" placeholder="设置登录密码" required minlength="6" />
        </div>
        <div class="free-tip">
          🎁 注册即享免费体验：痛点分析5次 + Listing生成3次
        </div>
        <div class="error-msg" v-if="error">{{ error }}</div>
        <button type="submit" class="btn btn-primary w-full" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          <span>{{ loading ? '注册中...' : '免费注册' }}</span>
        </button>
      </form>

      <!-- 套餐预览 -->
      <div class="pricing-preview">
        <div class="pricing-row" v-for="p in plans" :key="p.tier">
          <span class="p-tier">{{ p.label }}</span>
          <span class="p-price">{{ p.price }}</span>
          <span class="p-desc">{{ p.desc }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const auth = useAuthStore()

const mode = ref('login')
const email = ref('')
const password = ref('')
const name = ref('')
const loading = ref(false)
const error = ref('')

const plans = [
  { tier: 'free', label: '免费版', price: '0元', desc: '痛点5次·Listing3次' },
  { tier: 'basic', label: '基础版', price: '498元/月', desc: '200次/月·全功能' },
  { tier: 'pro', label: '专业版', price: '1280元/月', desc: '不限次数+投放优化' },
  { tier: 'enterprise', label: '企业版', price: '3980元/月', desc: '多店铺+1v1陪跑' },
]

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  const result = await auth.login(email.value, password.value).catch(e => ({ ok: false, error: e.message }))
  loading.value = false
  if (result.ok) {
    router.push('/home')
  } else {
    error.value = result.error || '登录失败'
  }
}

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  const result = await auth.register(email.value, password.value, name.value).catch(e => ({ ok: false, error: e.message }))
  loading.value = false
  if (result.ok) {
    router.push('/home')
  } else {
    error.value = result.error || '注册失败'
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #14532d 0%, #166534 50%, #15803d 100%);
  padding: 24px;
}

.login-card {
  background: #fff; border-radius: 16px; padding: 36px 32px;
  width: 100%; max-width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
}

.brand { text-align: center; margin-bottom: 24px; }
.brand-icon { font-size: 40px; display: block; margin-bottom: 8px; }
.brand-name { font-size: 24px; font-weight: 800; color: #14532d; }
.brand-sub { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

.tabs { display: flex; background: #f3f4f6; border-radius: 8px; padding: 3px; margin-bottom: 20px; }
.tab {
  flex: 1; padding: 8px; border: none; background: transparent; border-radius: 6px;
  font-size: 14px; font-weight: 600; cursor: pointer; color: var(--text-muted);
  transition: all .15s;
}
.tab.active { background: #fff; color: var(--green-dark); box-shadow: 0 1px 3px rgba(0,0,0,.1); }

.form { display: flex; flex-direction: column; gap: 12px; }
.w-full { width: 100%; margin-top: 4px; }

.free-tip {
  background: #f0fdf4; border: 1px solid var(--green-light); border-radius: 8px;
  padding: 8px 12px; font-size: 12px; color: var(--green-dark); font-weight: 500;
}

.error-msg {
  background: #fef2f2; border: 1px solid #fca5a5; color: #dc2626;
  padding: 8px 12px; border-radius: 6px; font-size: 13px;
}

.pricing-preview {
  margin-top: 20px; border-top: 1px solid var(--border); padding-top: 16px;
  display: flex; flex-direction: column; gap: 6px;
}
.pricing-row { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.p-tier { width: 60px; font-weight: 600; color: var(--text); }
.p-price { width: 90px; color: var(--green-dark); font-weight: 700; }
.p-desc { color: var(--text-muted); }
</style>
