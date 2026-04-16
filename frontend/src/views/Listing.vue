<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">✍️ 三农 Listing 全自动生成</h1>
      <p class="page-desc">填写产品信息，AI一键生成：标题 + 卖点 + 详情页 + 主图脚本 + 短视频口播 + 直播话术</p>
    </div>

    <div class="page-body">
      <div class="layout-grid">
        <!-- 左列：表单 -->
        <div class="left-col">
          <div class="card form-card">
            <h3 class="card-title">产品信息</h3>

            <div class="form-group">
              <label class="form-label">产品名称 <span class="required">*</span></label>
              <input v-model="form.product_name" class="form-input" placeholder="例如：赣南脐橙" />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="form-label">品类 <span class="required">*</span></label>
                <select v-model="form.category" class="form-select">
                  <option value="">请选择品类</option>
                  <option value="脐橙">脐橙</option>
                  <option value="苹果">苹果</option>
                  <option value="草莓">草莓</option>
                  <option value="樱桃">樱桃</option>
                  <option value="蓝莓">蓝莓</option>
                  <option value="猕猴桃">猕猴桃</option>
                  <option value="芒果">芒果</option>
                  <option value="桃子">桃子</option>
                  <option value="葡萄">葡萄</option>
                  <option value="西瓜">西瓜</option>
                  <option value="沃柑">沃柑</option>
                  <option value="石榴">石榴</option>
                  <option value="蔬菜">蔬菜</option>
                  <option value="粮油">粮油(大米)</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">目标平台</label>
                <select v-model="form.platform" class="form-select">
                  <option v-for="p in platforms" :key="p.value" :value="p.value">
                    {{ p.label }}（标题≤{{ p.title_limit }}字）
                  </option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="form-label">产地</label>
                <input v-model="form.origin" class="form-input" placeholder="例如：江西赣州" />
              </div>
              <div class="form-group">
                <label class="form-label">规格/重量</label>
                <input v-model="form.specification" class="form-input" placeholder="例如：5斤装" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="form-label">定价</label>
                <input v-model="form.price" class="form-input" placeholder="例如：29.9元/5斤" />
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">核心卖点描述</label>
              <textarea
                v-model="form.core_features"
                class="form-textarea"
                rows="2"
                placeholder="例如：高糖度12°以上，皮薄汁多，果肉细腻，无渣"
              ></textarea>
            </div>

            <div class="form-group">
              <label class="form-label">痛点摘要（来自痛点分析，可选）</label>
              <textarea
                v-model="form.pain_points_summary"
                class="form-textarea"
                rows="2"
                placeholder="粘贴痛点分析结果，AI会针对性生成内容..."
              ></textarea>
            </div>

            <button
              class="btn btn-primary w-full"
              @click="generate"
              :disabled="loading || !form.product_name || !form.category"
            >
              <span v-if="loading" class="loading-spinner"></span>
              <span v-if="loading">AI生成中（约20-40秒）...</span>
              <span v-else>🚀 一键生成全套 Listing</span>
            </button>
          </div>

          <!-- 合规检测 -->
          <div class="card compliance-card" v-if="result?.compliance">
            <h3 class="card-title">✅ 合规检测报告</h3>
            <div :class="['compliance-status', result.compliance.passed ? 'passed' : 'failed']">
              <span class="status-icon">{{ result.compliance.passed ? '✅' : '⚠️' }}</span>
              <div>
                <div class="status-text">{{ result.compliance.passed ? '合规通过' : '存在违规问题' }}</div>
                <div class="status-detail">
                  严重问题 {{ result.compliance.critical_count }} | 
                  警告 {{ result.compliance.warning_count }} | 
                  提示 {{ result.compliance.info_count }}
                </div>
              </div>
            </div>
            <div v-if="result.compliance.issues?.length" class="issues-list">
              <div
                v-for="(issue, idx) in result.compliance.issues"
                :key="idx"
                :class="['issue-item', `issue-${issue.severity}`]"
              >
                <div class="issue-header">
                  <span :class="['badge', issueBadge(issue.severity)]">{{ issueLabel(issue.severity) }}</span>
                  <span class="issue-field">{{ issue.field }}</span>
                </div>
                <div class="issue-text">违规内容：「{{ issue.matched_text }}」</div>
                <div class="issue-suggestion">建议：{{ issue.suggestion }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右列：生成结果 -->
        <div class="right-col" v-if="result">
          <!-- Tab切换 -->
          <div class="tabs-bar">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              :class="['tab-btn', { active: activeTab === tab.key }]"
              @click="activeTab = tab.key"
            >
              {{ tab.icon }} {{ tab.label }}
            </button>
          </div>

          <!-- 标题+卖点 -->
          <div v-show="activeTab === 'listing'" class="tab-content">
            <div class="result-section">
              <div class="rs-header">
                <span class="rs-label">📌 主标题</span>
                <button class="btn-copy" @click="copy(result.title)">复制</button>
              </div>
              <div class="rs-title">{{ result.title }}</div>
              <div class="title-meta">
                <span :class="['badge', titleLenBadge]">{{ result.title?.length || 0 }} 字</span>
                <span class="badge badge-gray">建议≤{{ platformLimit }}字</span>
              </div>
            </div>

            <div class="result-section" v-if="result.subtitle">
              <div class="rs-header">
                <span class="rs-label">📣 副标题</span>
                <button class="btn-copy" @click="copy(result.subtitle)">复制</button>
              </div>
              <div class="rs-content">{{ result.subtitle }}</div>
            </div>

            <div class="result-section">
              <div class="rs-header">
                <span class="rs-label">⭐ 核心卖点（5条）</span>
                <button class="btn-copy" @click="copy(result.selling_points?.join('\n'))">复制全部</button>
              </div>
              <ul class="sp-list">
                <li v-for="(sp, i) in result.selling_points" :key="i" class="sp-item">
                  <span class="sp-num">{{ i + 1 }}</span>
                  <span>{{ sp }}</span>
                </li>
              </ul>
            </div>

            <div class="result-section">
              <div class="rs-header">
                <span class="rs-label">🔑 SEO关键词</span>
                <button class="btn-copy" @click="copy(result.seo_keywords?.join(' '))">复制</button>
              </div>
              <div class="keywords-row">
                <span class="kw-tag" v-for="kw in result.seo_keywords" :key="kw">{{ kw }}</span>
              </div>
            </div>

            <div class="result-section" v-if="result.hashtags?.length">
              <div class="rs-header">
                <span class="rs-label"># 话题标签</span>
                <button class="btn-copy" @click="copy(result.hashtags?.join(' '))">复制</button>
              </div>
              <div class="keywords-row">
                <span class="kw-tag tag-blue" v-for="ht in result.hashtags" :key="ht">{{ ht }}</span>
              </div>
            </div>
          </div>

          <!-- 详情页 -->
          <div v-show="activeTab === 'detail'" class="tab-content">
            <template v-if="result.detail_page">
              <div class="result-section" v-for="(val, key) in result.detail_page" :key="key">
                <div class="rs-header">
                  <span class="rs-label">{{ detailLabels[key] || key }}</span>
                  <button class="btn-copy" @click="copy(val)">复制</button>
                </div>
                <div class="rs-content">{{ val }}</div>
              </div>
            </template>
          </div>

          <!-- 主图脚本 -->
          <div v-show="activeTab === 'image'" class="tab-content">
            <template v-if="result.main_image_script">
              <div class="result-section" v-for="(val, key) in result.main_image_script" :key="key">
                <div class="rs-header">
                  <span class="rs-label">{{ imageLabels[key] || key }}</span>
                  <button class="btn-copy" @click="copy(val)">复制</button>
                </div>
                <div class="rs-content">{{ val }}</div>
              </div>
            </template>
          </div>

          <!-- 短视频口播 -->
          <div v-show="activeTab === 'video'" class="tab-content">
            <template v-if="result.video_script">
              <div class="result-section" v-for="(val, key) in result.video_script" :key="key">
                <div class="rs-header">
                  <span class="rs-label">{{ videoLabels[key] || key }}</span>
                  <button class="btn-copy" @click="copy(val)">复制</button>
                </div>
                <div class="rs-content script-content">{{ val }}</div>
              </div>
            </template>
          </div>

          <!-- 直播话术 -->
          <div v-show="activeTab === 'live'" class="tab-content">
            <template v-if="result.live_script">
              <div class="result-section" v-for="(val, key) in result.live_script" :key="key">
                <div class="rs-header">
                  <span class="rs-label">{{ liveLabels[key] || key }}</span>
                  <button class="btn-copy" @click="copy(val)">复制</button>
                </div>
                <div class="rs-content script-content">{{ val }}</div>
              </div>
            </template>
          </div>

          <!-- 反馈栏 -->
          <div class="feedback-bar" v-if="result && !feedbackDone[`listing_${activeTab}`]">
            <span class="fb-label">这部分内容质量如何？</span>
            <button class="fb-btn usable" @click="submitFeedback('listing', 'usable')">✅ 直接可用</button>
            <button class="fb-btn edit" @click="submitFeedback('listing', 'needs_edit')">✏️ 改了能用</button>
            <button class="fb-btn bad" @click="submitFeedback('listing', 'unusable')">❌ 不能用</button>
          </div>
          <div class="fb-done" v-else-if="feedbackDone[`listing_${activeTab}`]">✅ 反馈已记录，感谢！</div>
        </div>

        <!-- 空状态右列 -->
        <div class="right-col empty-right" v-else>
          <div class="card empty-state" style="height:400px;display:flex;flex-direction:column;align-items:center;justify-content:center">
            <span class="empty-icon">✍️</span>
            <p>填写左侧表单后，点击生成按钮</p>
            <p style="font-size:12px;margin-top:8px;color:#9ca3af">将自动生成全套三农营销内容</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 复制成功提示 -->
    <div class="copy-toast" v-if="copyToast">✅ 已复制到剪贴板</div>

    <!-- 错误提示 -->
    <div class="error-toast" v-if="error">
      ⚠️ {{ error }}
      <button @click="error = ''" style="margin-left:8px;background:none;border:none;cursor:pointer;color:inherit">×</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { listingApi, feedbackApi } from '../api/index.js'

const route = useRoute()

const platforms = ref([
  { value: 'douyin', label: '抖音小店', title_limit: 30 },
  { value: 'pinduoduo', label: '拼多多', title_limit: 60 },
  { value: 'huinong', label: '惠农网', title_limit: 50 },
  { value: 'taobao', label: '淘宝', title_limit: 60 },
  { value: 'jd', label: '京东', title_limit: 60 },
])

const form = ref({
  product_name: route.query.product_name || '',
  category: route.query.category || '',
  origin: '',
  specification: '',
  price: '',
  core_features: '',
  platform: 'douyin',
  pain_points_summary: route.query.pain_summary || '',
})

const loading = ref(false)
const result = ref(null)
const error = ref('')
const copyToast = ref(false)
const activeTab = ref('listing')
const feedbackDone = ref({})

const tabs = [
  { key: 'listing', icon: '📋', label: 'Listing' },
  { key: 'detail', icon: '📄', label: '详情页' },
  { key: 'image', icon: '🖼️', label: '主图脚本' },
  { key: 'video', icon: '🎬', label: '短视频口播' },
  { key: 'live', icon: '🔴', label: '直播话术' },
]

const detailLabels = {
  product_intro: '📦 产品介绍',
  origin_story: '🌍 产地故事',
  quality_proof: '✅ 品质证明',
  delivery_info: '🚚 配送说明',
  after_sale: '🔒 售后保障',
}
const imageLabels = {
  scene_1: '主图1', scene_2: '主图2', scene_3: '主图3', scene_4: '主图4', scene_5: '主图5',
}
const videoLabels = {
  hook_0_3s: '⚡ 开场钩子（0-3s）',
  product_show_3_15s: '🍊 产品展示（3-15s）',
  trust_15_25s: '🤝 信任建立（15-25s）',
  cta_25_30s: '📣 行动引导（25-30s）',
  full_script: '📝 完整30秒口播稿',
}
const liveLabels = {
  opening: '🎤 直播开场',
  product_intro: '📦 产品介绍（2分钟）',
  pain_solve: '❓ 痛点解决',
  trust_build: '🤝 信任建立',
  urgency: '⏰ 紧迫感营造',
  price_anchor: '💰 价格锚定',
  closing: '🛒 催单成交',
  after_purchase: '⭐ 购后维护',
}

const platformLimit = computed(() => {
  return platforms.value.find(p => p.value === form.value.platform)?.title_limit || 60
})

const titleLenBadge = computed(() => {
  const len = result.value?.title?.length || 0
  if (len <= platformLimit.value) return 'badge-green'
  return 'badge-red'
})

const issueBadge = (sev) => {
  if (sev === 'critical') return 'badge-red'
  if (sev === 'warning') return 'badge-orange'
  return 'badge-gray'
}
const issueLabel = (sev) => {
  if (sev === 'critical') return '严重'
  if (sev === 'warning') return '警告'
  return '提示'
}

const generate = async () => {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const res = await listingApi.generate(form.value)
    if (res.code === 0) {
      result.value = res.data
      activeTab.value = 'listing'
    } else {
      error.value = res.message || '生成失败'
    }
  } catch (e) {
    error.value = e.message || '网络请求失败'
  } finally {
    loading.value = false
  }
}

const copy = async (text) => {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copyToast.value = true
    setTimeout(() => { copyToast.value = false }, 2000)
  } catch {
    // fallback
  }
}

const submitFeedback = async (contentType, rating) => {
  const key = `${contentType}_${activeTab.value}`
  feedbackDone.value[key] = true
  try {
    const fullText = activeTab.value === 'video'
      ? result.value?.video_script?.full_script || ''
      : activeTab.value === 'live'
        ? JSON.stringify(result.value?.live_script || {})
        : result.value?.title || ''
    await feedbackApi.submit({
      content_type: contentType,
      content_id: activeTab.value,
      product_name: form.value.product_name,
      category: form.value.category,
      rating,
      edited_text: rating === 'usable' ? fullText : '',
      comment: '',
    })
  } catch {}
}

onMounted(async () => {
  try {
    const res = await listingApi.getPlatforms()
    if (res.data?.length) platforms.value = res.data
  } catch {}
})
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; }

.layout-grid { display: grid; grid-template-columns: 360px 1fr; gap: 16px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.card-title { font-size: 15px; font-weight: 700; margin-bottom: 16px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.w-full { width: 100%; margin-top: 4px; }

/* Compliance */
.compliance-card { margin-top: 0; }
.compliance-status { display: flex; align-items: flex-start; gap: 10px; padding: 12px; border-radius: 8px; margin-bottom: 12px; }
.compliance-status.passed { background: var(--green-bg); }
.compliance-status.failed { background: #fef2f2; }
.status-icon { font-size: 20px; }
.status-text { font-weight: 700; font-size: 14px; }
.status-detail { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.issues-list { display: flex; flex-direction: column; gap: 8px; }
.issue-item { border-radius: 8px; padding: 10px 12px; font-size: 12px; }
.issue-critical { background: #fef2f2; border: 1px solid #fca5a5; }
.issue-warning { background: #fffbeb; border: 1px solid #fde68a; }
.issue-info { background: #f0f9ff; border: 1px solid #bae6fd; }
.issue-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.issue-field { font-weight: 600; color: var(--text-muted); }
.issue-text { color: var(--text); margin-bottom: 4px; }
.issue-suggestion { color: var(--text-muted); }

/* Tabs */
.tabs-bar {
  display: flex; gap: 4px; padding: 4px; background: #f3f4f6;
  border-radius: 10px; margin-bottom: 12px; flex-wrap: wrap;
}
.tab-btn {
  flex: 1; padding: 8px 12px; border: none; background: transparent; border-radius: 7px;
  font-size: 13px; font-weight: 600; cursor: pointer; color: var(--text-muted);
  transition: all .15s ease; white-space: nowrap;
}
.tab-btn.active { background: #fff; color: var(--green-dark); box-shadow: var(--shadow); }

/* Result sections */
.tab-content { display: flex; flex-direction: column; gap: 12px; }
.result-section { background: #fff; border-radius: 10px; border: 1px solid var(--border); overflow: hidden; }
.rs-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; background: #f9fafb; border-bottom: 1px solid var(--border);
}
.rs-label { font-size: 13px; font-weight: 700; }
.btn-copy {
  font-size: 12px; padding: 3px 10px; border: 1px solid var(--border);
  border-radius: 5px; background: #fff; cursor: pointer; color: var(--text-muted);
  transition: all .1s; font-weight: 500;
}
.btn-copy:hover { border-color: var(--green-primary); color: var(--green-dark); }
.rs-title { padding: 14px; font-size: 16px; font-weight: 700; line-height: 1.5; }
.title-meta { display: flex; gap: 6px; padding: 0 14px 12px; }
.rs-content { padding: 12px 14px; font-size: 13px; line-height: 1.8; color: var(--text); white-space: pre-wrap; }
.script-content { background: #fafafa; }

.sp-list { list-style: none; padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; }
.sp-item { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; line-height: 1.6; }
.sp-num {
  width: 22px; height: 22px; background: var(--green-primary); color: #fff;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0; margin-top: 1px;
}

.keywords-row { padding: 12px 14px; display: flex; flex-wrap: wrap; gap: 8px; }
.kw-tag { background: var(--green-light); color: var(--green-dark); border-radius: 6px; padding: 4px 10px; font-size: 12px; }
.tag-blue { background: #dbeafe; color: #1d4ed8; }

.empty-right {}

/* Feedback */
.feedback-bar { display: flex; align-items: center; gap: 6px; padding: 12px 14px; background: #f9fafb; border-radius: 10px; border: 1px solid var(--border); flex-wrap: wrap; }
.fb-label { font-size: 12px; color: var(--text-muted); margin-right: 4px; }
.fb-btn { font-size: 11px; padding: 4px 10px; border-radius: 6px; border: 1px solid; cursor: pointer; font-weight: 600; }
.fb-btn.usable { border-color: var(--green-light); color: var(--green-dark); background: var(--green-bg); }
.fb-btn.edit { border-color: #fde68a; color: #92400e; background: #fffbeb; }
.fb-btn.bad { border-color: #fca5a5; color: #dc2626; background: #fef2f2; }
.fb-done { font-size: 12px; color: var(--green-dark); padding: 10px 14px; }

/* Toasts */
.copy-toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  background: #f0fdf4; border: 1px solid var(--green-light); color: var(--green-dark);
  padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 600;
  z-index: 999; box-shadow: var(--shadow-md);
}
.error-toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  background: #fef2f2; border: 1px solid #fca5a5; color: #dc2626;
  padding: 10px 16px; border-radius: 8px; font-size: 13px; z-index: 999;
  box-shadow: var(--shadow-md);
}
</style>
