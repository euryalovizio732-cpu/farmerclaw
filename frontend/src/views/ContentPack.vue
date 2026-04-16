<template>
  <div class="page">
    <div class="page-header">
      <div class="header-top">
        <div>
          <h1 class="page-title">📦 今日内容包</h1>
          <p class="page-desc">输入产品，3分钟拿到今天的选题+口播稿+直播话术，直接用</p>
        </div>
        <!-- 节气提示 -->
        <div class="season-badge" v-if="seasonInfo.season">
          <span class="season-icon">🌿</span>
          <div>
            <div class="season-name">{{ seasonInfo.season }} · {{ seasonInfo.solar_term }}</div>
            <div class="season-angle">{{ seasonInfo.angle }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-body">
      <!-- 表单 -->
      <div class="card form-card" v-if="!result">
        <div class="form-mode-toggle">
          <h3 class="card-title">今天卖什么？</h3>
          <div class="mode-switch">
            <button :class="['mode-btn', {active: quickMode}]" @click="quickMode=true">快速模式</button>
            <button :class="['mode-btn', {active: !quickMode}]" @click="quickMode=false">详细填写</button>
          </div>
        </div>

        <div v-if="draftEntry || recentForms.length" class="history-bar">
          <div class="history-head">
            <span class="history-title">最近使用</span>
            <router-link to="/history" class="history-link">查看全部历史</router-link>
          </div>
          <div class="history-chips">
            <button v-if="draftEntry" class="history-chip draft-chip" @click="restoreDraft">
              <span class="history-chip-main">继续上次填写</span>
              <span class="history-chip-meta">{{ draftLabel(draftEntry) }}</span>
            </button>
            <button v-for="item in recentForms" :key="item.id" class="history-chip" @click="applyRecentForm(item)">
              <span class="history-chip-main">{{ historyLabel(item) }}</span>
              <span v-if="historyMeta(item)" class="history-chip-meta">{{ historyMeta(item) }}</span>
            </button>
          </div>
        </div>

        <!-- 快速模式 -->
        <div v-if="quickMode" class="quick-mode">
          <div class="form-group">
            <label class="form-label">一句话描述你的产品</label>
            <textarea v-model="quickText" class="form-input quick-textarea" rows="2"
              placeholder="例如：我卖赣南脐橙，29.9元5斤，江西赣州发货，皮薄汁多坏果包赔"></textarea>
          </div>
          <button class="btn btn-secondary parse-btn" @click="quickParse" :disabled="parsing || !quickText.trim()">
            {{ parsing ? '解析中...' : '🔍 智能解析' }}
          </button>
          <!-- 解析结果预览 -->
          <div class="parsed-preview" v-if="parsedOk">
            <div class="parsed-tag" v-if="form.product_name"><b>产品</b> {{ form.product_name }}</div>
            <div class="parsed-tag" v-if="form.category"><b>品类</b> {{ form.category }}</div>
            <div class="parsed-tag" v-if="form.origin"><b>产地</b> {{ form.origin }}</div>
            <div class="parsed-tag" v-if="form.price"><b>价格</b> {{ form.price }}</div>
            <div class="parsed-tag" v-if="form.core_features"><b>卖点</b> {{ form.core_features }}</div>
            <span class="parsed-hint">解析有误？点「详细填写」修改</span>
          </div>
        </div>

        <!-- 详细模式 -->
        <div v-else>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">产品名称 <span class="required">*</span></label>
              <input v-model="form.product_name" class="form-input" placeholder="例如：赣南脐橙" />
            </div>
            <div class="form-group">
              <label class="form-label">品类 <span class="required">*</span></label>
              <select v-model="form.category" class="form-select">
                <option value="">选择品类</option>
                <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">产地</label>
              <input v-model="form.origin" class="form-input" placeholder="例如：江西赣州" />
            </div>
            <div class="form-group">
              <label class="form-label">定价</label>
              <input v-model="form.price" class="form-input" placeholder="例如：29.9元/5斤" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">核心卖点（选填）</label>
            <input v-model="form.core_features" class="form-input" placeholder="例如：高糖度，皮薄汁多，坏果包赔" />
          </div>
        </div>

        <button class="btn btn-primary generate-btn" @click="generate" :disabled="loading || !form.product_name || !form.category">
          <span v-if="loading" class="loading-spinner"></span>
          <span>{{ loading ? 'AI生成中（约30-60秒）...' : '📦 一键生成今日内容包' }}</span>
        </button>
      </div>

      <!-- 生成中进度 -->
      <div class="card progress-card" v-if="loading">
        <div class="progress-steps">
          <div :class="['ps', {done: pstage>=1, active: pstage===0}]">
            <span>{{ pstage>=1?'✅':'⏳' }}</span><span>节气分析</span>
          </div>
          <span class="ps-arrow">→</span>
          <div :class="['ps', {done: pstage>=2, active: pstage===1}]">
            <span>{{ pstage>=2?'✅':'⭕' }}</span><span>选题生成</span>
          </div>
          <span class="ps-arrow">→</span>
          <div :class="['ps', {done: pstage>=3, active: pstage===2}]">
            <span>{{ pstage>=3?'✅':'⭕' }}</span><span>口播稿生成</span>
          </div>
          <span class="ps-arrow">→</span>
          <div :class="['ps', {done: pstage>=4, active: pstage===3}]">
            <span>{{ pstage>=4?'✅':'⭕' }}</span><span>直播话术</span>
          </div>
        </div>
        <p class="progress-tip">{{ progressTips[pstage] || '处理中...' }}</p>
      </div>

      <!-- 结果区 -->
      <template v-if="result && !loading">
        <!-- 今日提示条 -->
        <div class="today-bar">
          <span class="today-date">📅 {{ result.date }}</span>
          <span v-if="savedAt" class="saved-badge">💾 上次生成 {{ savedAt }}</span>
          <span class="today-tip">💡 {{ result.today?.tip }}</span>
          <button class="btn btn-secondary" @click="exportAll">📋 导出全部</button>
          <button class="btn btn-secondary reset-btn" @click="reset">重新生成</button>
        </div>

        <!-- Tab 切换 -->
        <div class="tabs-nav">
          <button v-for="tab in tabs" :key="tab.key" :class="['tab-btn', {active: activeTab===tab.key}]" @click="activeTab=tab.key">
            {{ tab.icon }} {{ tab.label }}
          </button>
        </div>

        <!-- Tab: 选题 -->
        <div v-if="activeTab==='topics'" class="tab-content">
          <div class="topic-cards">
            <div v-for="topic in result.topics" :key="topic.topic_id" class="topic-card">
              <div class="topic-header">
                <span class="topic-type-badge">{{ topic.type }}</span>
                <span class="topic-cr">完播预估：{{ topic.estimated_completion_rate?.split('，')[0] || '中' }}</span>
              </div>
              <div class="topic-title">{{ topic.title }}</div>
              <div class="topic-meta">
                <div class="meta-row"><span class="ml">📸 封面建议</span><span>{{ topic.first_frame }}</span></div>
                <div class="meta-row"><span class="ml">🎬 拍摄角度</span><span>{{ topic.shooting_angle }}</span></div>
                <div class="meta-row"><span class="ml">⚡ 爆点</span><span>{{ topic.core_conflict }}</span></div>
              </div>
              <div class="kw-tags" v-if="topic.oral_keywords?.length">
                <span class="kw-tag" v-for="kw in topic.oral_keywords" :key="kw">{{ kw }}</span>
              </div>
              <div class="topic-actions">
                <button class="btn-use" @click="useContent('topic', topic.topic_id, topic.title)">📹 用这个选题</button>
                <button class="btn-copy-sm" @click="copy(topic.title)">复制标题</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 口播稿 -->
        <div v-if="activeTab==='scripts'" class="tab-content">
          <div class="script-tip">💡 以下 3 条口播稿对应 3 个选题方向，可直接念，约 30 秒 · 用完请评价帮助改进</div>
          <div class="script-cards">
            <div v-for="script in result.scripts" :key="script.topic_id" class="script-card">
              <div class="script-header">
                <span class="script-no">口播 {{ script.topic_id }}</span>
                <span class="script-type">{{ script.topic_type }}</span>
                <span v-if="script.formula_type" class="formula-badge">{{ script.formula_type }}型</span>
                <button class="btn-copy-sm" @click="copy(script.full_script)">复制全文</button>
              </div>
              <div class="script-topic-ref">对应选题：{{ script.topic_title }}</div>
              <div class="script-segments">
                <div class="seg"><span class="seg-tag hook">钩子 0-3s</span><span>{{ script.hook_0_3s }}</span></div>
                <div class="seg"><span class="seg-tag product">产品 3-15s</span><span>{{ script.product_3_15s }}</span></div>
                <div class="seg"><span class="seg-tag trust">信任 15-25s</span><span>{{ script.trust_15_25s }}</span></div>
                <div class="seg"><span class="seg-tag cta">CTA 25-30s</span><span>{{ script.cta_25_30s }}</span></div>
              </div>
              <div class="script-full">
                <div class="full-label">完整口播稿（可直接念）</div>
                <div class="full-text">{{ script.full_script }}</div>
              </div>
              <!-- 操作按钮 -->
              <div class="action-row">
                <button class="btn-use btn-use-lg" @click="useContent('script', script.topic_id, script.full_script)">
                  📹 复制去拍
                </button>
                <div class="fb-secondary" v-if="!feedbackDone[`script_${script.topic_id}`]">
                  <button class="fb-btn edit" @click="submitFeedback('script', script.topic_id, 'needs_edit', script.full_script)">✏️ 改了能用</button>
                  <button class="fb-btn bad" @click="submitFeedback('script', script.topic_id, 'unusable', script.full_script)">❌ 不能用</button>
                </div>
                <span class="fb-done-inline" v-if="usedContent[`script_${script.topic_id}`]">✅ 已复制，期待好结果！</span>
                <span class="fb-done-inline" v-else-if="feedbackDone[`script_${script.topic_id}`]">📝 反馈已记录</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 直播话术 -->
        <div v-if="activeTab==='live'" class="tab-content">
          <div class="script-tip">💡 以下话术模块可自由拼接，组合成 2 小时直播话术</div>
          <div v-for="(modules, mtype) in result.live_modules" :key="mtype" class="module-section">
            <div class="module-type-label">{{ moduleLabels[mtype] || mtype }}</div>
            <div class="module-cards">
              <div v-for="m in modules" :key="m.id" class="module-card">
                <div class="module-header">
                  <span class="module-name">{{ m.name }}</span>
                  <button class="btn-copy-sm" @click="copy(m.script)">复制</button>
                </div>
                <div class="module-script">{{ m.script }}</div>
                <div class="module-tips">💡 {{ m.tips }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: 话题标签 -->
        <div v-if="activeTab==='hashtags'" class="tab-content">
          <div class="card">
            <div class="ht-header">
              <h3 class="card-title">今日推荐话题标签</h3>
              <button class="btn btn-secondary" @click="copy(result.hashtags?.join(' '))">一键复制全部</button>
            </div>
            <div class="ht-tags">
              <div v-for="ht in result.hashtags" :key="ht" class="ht-tag" @click="copy(ht)">
                {{ ht }}
              </div>
            </div>
            <p class="ht-tip">点击单个标签即可复制，发布时粘贴到抖音文案末尾</p>

            <!-- 节气热点产品 -->
            <div class="season-products" v-if="result.today?.hot_products?.length">
              <div class="sp-label">{{ result.today.season }} 时令热推产品</div>
              <div class="sp-tags">
                <span v-for="p in result.today.hot_products" :key="p" class="sp-tag">{{ p }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 初始空状态 -->
      <div class="card empty-state" v-if="!loading && !result">
        <span class="empty-icon">📦</span>
        <p>填写产品信息，生成今天的内容包</p>
        <div class="empty-flow">
          <span>选题 →</span><span>口播稿 →</span><span>直播话术 →</span><span>话题标签</span>
        </div>
      </div>
    </div>

    <div class="copy-toast" v-if="copyToast">✅ 已复制</div>
    <div class="error-toast" v-if="errorMsg">⚠️ {{ errorMsg }} <button @click="errorMsg=''" style="margin-left:8px;background:none;border:none;cursor:pointer;color:inherit">×</button></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { feedbackApi } from '../api/index.js'

const http = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api', timeout: 240000 })

const categories = ['脐橙', '苹果', '草莓', '樱桃', '蓝莓', '猕猴桃', '芒果', '桃子', '葡萄', '西瓜', '沃柑', '石榴', '蔬菜', '粮油']
const form = ref({ product_name: '', category: '', origin: '', price: '', core_features: '' })
const loading = ref(false)
const result = ref(null)
const errorMsg = ref('')
const copyToast = ref(false)
const pstage = ref(0)
const seasonInfo = ref({})
const activeTab = ref('topics')
const quickMode = ref(true)
const quickText = ref('')
const parsing = ref(false)
const parsedOk = ref(false)
const usedContent = ref({})
const savedAt = ref('')
const recentForms = ref([])
const draftEntry = ref(null)
const CACHE_KEY = 'fc_content_pack_last'
const DRAFT_KEY = 'fc_content_pack_draft'
const RECENT_KEY = 'fc_content_pack_recent'

const tabs = [
  { key: 'topics', label: '3条选题', icon: '💡' },
  { key: 'scripts', label: '3条口播稿', icon: '🎙️' },
  { key: 'live', label: '直播话术积木', icon: '🔴' },
  { key: 'hashtags', label: '话题标签', icon: '#' },
]

const moduleLabels = {
  opening: '🟢 开场话术（选1条）',
  product_intro: '📦 产品介绍（必用）',
  interaction: '💬 互动模块（穿插使用）',
  urgency: '⏰ 紧迫感模块（促成交时用）',
  checkout: '💰 催单成交（收尾时用）',
}

const progressTips = ['正在分析当前节气时令...', '正在生成3条爆款选题...', '正在生成口播稿...', '正在整理直播话术积木...']

const feedbackDone = ref({})
const progressInterval = ref(null)

const sanitizeForm = (data = {}) => ({
  product_name: (data.product_name || '').trim(),
  category: (data.category || '').trim(),
  origin: (data.origin || '').trim(),
  price: (data.price || '').trim(),
  core_features: (data.core_features || '').trim(),
})

const hasUsableForm = (data = {}) => {
  const cleaned = sanitizeForm(data)
  return !!(cleaned.product_name || cleaned.category || cleaned.origin || cleaned.price || cleaned.core_features)
}

const buildHistoryId = (data = {}) => {
  const cleaned = sanitizeForm(data)
  return [cleaned.product_name, cleaned.category, cleaned.origin, cleaned.price, cleaned.core_features].join('|')
}

const historyLabel = (item) => item.product_name || item.category || '未命名产品'
const historyMeta = (item) => [item.category, item.origin, item.price].filter(Boolean).join(' · ')
const draftLabel = (item) => historyMeta(item.form || item) || '点一下恢复填写内容'

const persistDraft = () => {
  try {
    const draft = {
      form: sanitizeForm(form.value),
      quickText: quickText.value.trim(),
      quickMode: quickMode.value,
      updated_at: new Date().toISOString(),
    }
    if (hasUsableForm(draft.form) || draft.quickText) {
      draftEntry.value = draft
      localStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
    } else {
      draftEntry.value = null
      localStorage.removeItem(DRAFT_KEY)
    }
  } catch {}
}

const saveRecentForm = (source = form.value) => {
  const cleaned = sanitizeForm(source)
  if (!hasUsableForm(cleaned)) return
  const entry = {
    ...cleaned,
    id: buildHistoryId(cleaned),
    updated_at: new Date().toISOString(),
  }
  const next = [entry, ...recentForms.value.filter(item => item.id !== entry.id)].slice(0, 6)
  recentForms.value = next
  try { localStorage.setItem(RECENT_KEY, JSON.stringify(next)) } catch {}
}

const applyRecentForm = (item) => {
  Object.assign(form.value, sanitizeForm(item))
  quickMode.value = false
  parsedOk.value = false
  errorMsg.value = ''
}

const restoreDraft = () => {
  if (!draftEntry.value) return
  Object.assign(form.value, sanitizeForm(draftEntry.value.form || draftEntry.value))
  quickText.value = draftEntry.value.quickText || ''
  quickMode.value = typeof draftEntry.value.quickMode === 'boolean' ? draftEntry.value.quickMode : quickMode.value
  parsedOk.value = false
  errorMsg.value = ''
}

const generate = async () => {
  loading.value = true
  errorMsg.value = ''
  result.value = null
  pstage.value = 0
  activeTab.value = 'topics'

  progressInterval.value = setInterval(() => {
    pstage.value = Math.min(pstage.value + 1, 3)
  }, 10000)

  try {
    const token = localStorage.getItem('fc_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await http.post('/content-pack/generate', form.value, { headers })
    if (res.data.code === 0) {
      result.value = res.data.data
      pstage.value = 4
      const ts = new Date().toLocaleString('zh-CN', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' })
      savedAt.value = ts
      saveRecentForm(form.value)
      try { localStorage.setItem(CACHE_KEY, JSON.stringify({ result: res.data.data, form: form.value, savedAt: ts })) } catch {}
    } else {
      errorMsg.value = res.data.message || '生成失败'
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || e.message || '请求失败'
  } finally {
    clearInterval(progressInterval.value)
    loading.value = false
  }
}

const reset = () => { result.value = null; pstage.value = 0; feedbackDone.value = {}; usedContent.value = {}; savedAt.value = ''; try { localStorage.removeItem(CACHE_KEY) } catch {} }

const quickParse = async () => {
  parsing.value = true
  parsedOk.value = false
  errorMsg.value = ''
  try {
    const res = await http.post('/content-pack/quick-parse', { text: quickText.value })
    if (res.data.code === 0) {
      const d = res.data.data
      form.value.product_name = d.product_name || ''
      form.value.category = d.category || ''
      form.value.origin = d.origin || ''
      form.value.price = d.price || ''
      form.value.core_features = d.core_features || ''
      parsedOk.value = true
    } else {
      errorMsg.value = res.data.message || '解析失败'
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || '解析失败，请手动填写'
  } finally {
    parsing.value = false
  }
}

const useContent = async (type, id, text) => {
  await copy(text)
  const key = `${type}_${id}`
  usedContent.value[key] = true
  try {
    await feedbackApi.submit({
      content_type: type,
      content_id: String(id),
      product_name: form.value.product_name,
      category: form.value.category,
      rating: 'used_to_shoot',
      edited_text: '',
      comment: '',
    })
  } catch {}
}

const exportAll = async () => {
  if (!result.value) return
  const r = result.value
  let text = `【今日内容包】${r.product_name}  ${r.date}\n`
  text += '═'.repeat(40) + '\n\n'
  if (r.topics?.length) {
    r.topics.forEach((t, i) => {
      text += `▎选题${i + 1}：${t.title}\n`
      if (t.first_frame) text += `  封面建议：${t.first_frame}\n`
      if (t.shooting_angle) text += `  拍摄角度：${t.shooting_angle}\n`
      if (t.core_conflict) text += `  爆点：${t.core_conflict}\n`
      text += '\n'
    })
  }
  if (r.scripts?.length) {
    text += '─'.repeat(30) + '\n'
    r.scripts.forEach((s, i) => {
      text += `▎口播稿${i + 1}（对应选题：${s.topic_title || ''}）\n`
      text += `${s.full_script}\n\n`
    })
  }
  if (r.live_modules) {
    text += '─'.repeat(30) + '\n'
    text += '▎直播话术\n'
    for (const [mtype, modules] of Object.entries(r.live_modules)) {
      const label = moduleLabels[mtype] || mtype
      text += `\n【${label}】\n`
      modules.forEach(m => { text += `● ${m.name}：${m.script}\n` })
    }
    text += '\n'
  }
  if (r.hashtags?.length) {
    text += '─'.repeat(30) + '\n'
    text += '▎话题标签\n' + r.hashtags.join('  ') + '\n'
  }
  await copy(text)
}

const submitFeedback = async (type, id, rating, text) => {
  const key = `${type}_${id}`
  feedbackDone.value[key] = true
  try {
    await feedbackApi.submit({
      content_type: type,
      content_id: String(id),
      product_name: form.value.product_name,
      category: form.value.category,
      rating,
      edited_text: '',
      comment: '',
    })
  } catch {}
}

const copy = async (text) => {
  if (!text) return
  await navigator.clipboard.writeText(text).catch(() => {})
  copyToast.value = true
  setTimeout(() => { copyToast.value = false }, 2000)
}

watch([form, quickText, quickMode], () => {
  persistDraft()
}, { deep: true })

onMounted(async () => {
  let restoredResult = false
  try {
    const res = await http.get('/content-pack/season')
    if (res.data.code === 0) seasonInfo.value = res.data.data
  } catch {}
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    if (cached) {
      const { result: r, form: f, savedAt: s } = JSON.parse(cached)
      if (r) { result.value = r; pstage.value = 4; savedAt.value = s || ''; restoredResult = true }
      if (f) Object.assign(form.value, f)
    }
  } catch {}
  try {
    const recent = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
    recentForms.value = Array.isArray(recent) ? recent : []
  } catch {}
  if (!restoredResult) {
    try {
      const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null')
      draftEntry.value = draft
      if (draft) restoreDraft()
    } catch {}
  } else {
    try {
      draftEntry.value = JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null')
    } catch {}
  }
})
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; display: flex; flex-direction: column; gap: 16px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.card-title { font-size: 15px; font-weight: 700; margin-bottom: 14px; }

.header-top { display: flex; justify-content: space-between; align-items: flex-start; }
.season-badge { display: flex; align-items: center; gap: 10px; background: var(--green-bg); border: 1px solid var(--green-light); border-radius: 10px; padding: 10px 14px; }
.season-icon { font-size: 24px; }
.season-name { font-size: 13px; font-weight: 700; color: var(--green-dark); }
.season-angle { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.form-mode-toggle { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.form-mode-toggle .card-title { margin-bottom: 0; }
.mode-switch { display: flex; gap: 4px; background: #f1f5f9; border-radius: 8px; padding: 3px; }
.mode-btn { padding: 6px 14px; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; background: transparent; color: var(--text-muted); transition: all .15s; }
.mode-btn.active { background: #fff; color: var(--green-dark); box-shadow: 0 1px 3px rgba(0,0,0,.1); }

.history-bar { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; padding: 12px; border: 1px dashed var(--border); border-radius: 10px; background: #f8fafc; }
.history-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
.history-title { font-size: 12px; font-weight: 700; color: var(--text-muted); }
.history-link { font-size: 12px; font-weight: 600; color: var(--green-dark); text-decoration: none; }
.history-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.history-chip { display: flex; align-items: center; gap: 6px; max-width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 999px; background: #fff; cursor: pointer; transition: all .15s; }
.history-chip:hover { background: var(--green-bg); border-color: var(--green-light); }
.draft-chip { background: var(--green-bg); border-color: var(--green-light); }
.history-chip-main { font-size: 12px; font-weight: 700; color: var(--text); }
.history-chip-meta { font-size: 11px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.quick-mode { display: flex; flex-direction: column; gap: 10px; }
.quick-textarea { resize: none; font-size: 14px; line-height: 1.6; }
.parse-btn { align-self: flex-start; }
.parsed-preview { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 10px; background: var(--green-bg); border: 1px solid var(--green-light); border-radius: 8px; }
.parsed-tag { font-size: 12px; background: #fff; padding: 4px 10px; border-radius: 6px; border: 1px solid var(--border); }
.parsed-tag b { color: var(--text-muted); margin-right: 4px; font-weight: 600; }
.parsed-hint { font-size: 11px; color: var(--text-muted); margin-left: auto; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.generate-btn { width: 100%; margin-top: 8px; padding: 14px; font-size: 15px; }

/* Progress */
.progress-card { text-align: center; }
.progress-steps { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.ps { display: flex; align-items: center; gap: 5px; font-size: 13px; font-weight: 600; color: var(--text-muted); }
.ps.done { color: var(--green-dark); }
.ps.active { color: var(--orange-primary); }
.ps-arrow { color: var(--text-muted); }
.progress-tip { font-size: 13px; color: var(--text-muted); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{opacity:1;}50%{opacity:.4;} }

/* Today bar */
.today-bar { display: flex; align-items: center; gap: 12px; background: var(--green-bg); border: 1px solid var(--green-light); border-radius: 10px; padding: 10px 16px; flex-wrap: wrap; }
.today-date { font-size: 13px; font-weight: 700; color: var(--green-dark); }
.saved-badge { font-size: 11px; color: var(--text-muted); background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 2px 8px; }
.today-tip { flex: 1; font-size: 13px; color: var(--text); }
.reset-btn { margin-left: auto; }

/* Tabs */
.tabs-nav { display: flex; gap: 8px; flex-wrap: wrap; }
.tab-btn { padding: 8px 16px; border: 1px solid var(--border); border-radius: 8px; background: #fff; font-size: 13px; font-weight: 600; cursor: pointer; color: var(--text-muted); transition: all .15s; }
.tab-btn.active { background: var(--green-primary); color: #fff; border-color: var(--green-primary); }
.tab-content { display: flex; flex-direction: column; gap: 12px; }

/* Topics */
.topic-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.topic-card { background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.topic-header { display: flex; justify-content: space-between; align-items: center; }
.topic-type-badge { background: var(--orange-light); color: #c2410c; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
.topic-cr { font-size: 11px; color: var(--green-dark); font-weight: 600; }
.topic-title { font-size: 15px; font-weight: 700; line-height: 1.5; }
.topic-meta { display: flex; flex-direction: column; gap: 6px; }
.meta-row { display: flex; gap: 8px; font-size: 12px; }
.ml { color: var(--text-muted); font-weight: 600; white-space: nowrap; width: 70px; }
.kw-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.kw-tag { background: var(--green-bg); color: var(--green-dark); padding: 2px 7px; border-radius: 4px; font-size: 11px; }
.topic-actions { display: flex; gap: 8px; align-items: center; margin-top: 4px; }

/* 📹 Use buttons */
.btn-use { padding: 5px 14px; border: 1px solid var(--green-primary); border-radius: 6px; background: var(--green-bg); color: var(--green-dark); font-size: 12px; font-weight: 700; cursor: pointer; transition: all .15s; }
.btn-use:hover { background: var(--green-primary); color: #fff; }
.btn-use-lg { padding: 8px 20px; font-size: 13px; }
.action-row { display: flex; align-items: center; gap: 10px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); flex-wrap: wrap; }
.fb-secondary { display: flex; gap: 6px; }
.fb-done-inline { font-size: 12px; color: var(--green-dark); font-weight: 600; }

/* Scripts */
.script-tip { font-size: 12px; color: var(--text-muted); background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 8px 12px; }
.script-cards { display: flex; flex-direction: column; gap: 14px; }
.feedback-row { display: flex; align-items: center; gap: 6px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); flex-wrap: wrap; }
.fb-label { font-size: 12px; color: var(--text-muted); }
.fb-btn { font-size: 11px; padding: 4px 10px; border-radius: 6px; border: 1px solid; cursor: pointer; font-weight: 600; }
.fb-btn.usable { border-color: var(--green-light); color: var(--green-dark); background: var(--green-bg); }
.fb-btn.edit { border-color: #fde68a; color: #92400e; background: #fffbeb; }
.fb-btn.bad { border-color: #fca5a5; color: #dc2626; background: #fef2f2; }
.fb-done { font-size: 12px; color: var(--green-dark); margin-top: 10px; }
.formula-badge { font-size: 10px; padding: 2px 6px; background: #ede9fe; color: #6d28d9; border-radius: 4px; }

.script-card { background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
.script-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.script-no { font-size: 14px; font-weight: 800; color: var(--green-dark); }
.script-type { font-size: 12px; background: var(--green-light); color: var(--green-dark); padding: 2px 8px; border-radius: 4px; }
.script-topic-ref { font-size: 11px; color: var(--text-muted); margin-bottom: 10px; }
.script-segments { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.seg { display: flex; gap: 8px; font-size: 12px; align-items: flex-start; background: #f9fafb; border-radius: 6px; padding: 8px; }
.seg-tag { font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 3px; white-space: nowrap; }
.seg-tag.hook { background: #fef3c7; color: #92400e; }
.seg-tag.product { background: var(--green-bg); color: var(--green-dark); }
.seg-tag.trust { background: #eff6ff; color: #1d4ed8; }
.seg-tag.cta { background: #fce7f3; color: #9d174d; }
.script-full { background: #f9fafb; border-radius: 8px; padding: 12px; }
.full-label { font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px; }
.full-text { font-size: 13px; line-height: 1.8; white-space: pre-wrap; }

/* Live Modules */
.module-section { margin-bottom: 16px; }
.module-type-label { font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.module-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }
.module-card { background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 12px; }
.module-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.module-name { font-size: 13px; font-weight: 700; }
.module-script { font-size: 12px; line-height: 1.7; margin-bottom: 6px; }
.module-tips { font-size: 11px; color: var(--text-muted); }

/* Hashtags */
.ht-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.ht-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.ht-tag { background: var(--green-bg); border: 1px solid var(--green-light); color: var(--green-dark); padding: 6px 14px; border-radius: 99px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all .15s; }
.ht-tag:hover { background: var(--green-primary); color: #fff; }
.ht-tip { font-size: 11px; color: var(--text-muted); }
.season-products { margin-top: 16px; border-top: 1px solid var(--border); padding-top: 12px; }
.sp-label { font-size: 12px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px; }
.sp-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.sp-tag { background: var(--orange-light); color: #c2410c; padding: 3px 10px; border-radius: 4px; font-size: 12px; }

/* Empty */
.empty-state { text-align: center; padding: 48px; }
.empty-icon { font-size: 48px; display: block; margin-bottom: 12px; }
.empty-flow { display: flex; justify-content: center; gap: 12px; margin-top: 12px; font-size: 13px; color: var(--text-muted); }

/* Copy button */
.btn-copy-sm { font-size: 11px; padding: 3px 10px; border: 1px solid var(--border); border-radius: 4px; background: #fff; cursor: pointer; color: var(--text-muted); }
.btn-copy-sm:hover { background: var(--green-bg); color: var(--green-dark); border-color: var(--green-light); }

/* Toasts */
.copy-toast, .error-toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); padding: 10px 20px; border-radius: 8px; font-size: 13px; z-index: 999; box-shadow: 0 4px 12px rgba(0,0,0,.15); }
.copy-toast { background: #f0fdf4; border: 1px solid var(--green-light); color: var(--green-dark); }
.error-toast { background: #fef2f2; border: 1px solid #fca5a5; color: #dc2626; display: flex; align-items: center; }
</style>
