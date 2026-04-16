<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">⚡ 全流程自动化</h1>
      <p class="page-desc">输入产品信息，AI 自动完成：痛点挖掘 → Listing生成 → 合规校验，一次搞定</p>
    </div>

    <div class="page-body">
      <!-- 表单 -->
      <div class="card" v-if="!result">
        <h3 class="card-title">产品信息</h3>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">产品名称 <span class="required">*</span></label>
            <input v-model="form.product_name" class="form-input" placeholder="例如：赣南脐橙" />
          </div>
          <div class="form-group">
            <label class="form-label">品类 <span class="required">*</span></label>
            <select v-model="form.category" class="form-select">
              <option value="">请选择品类</option>
              <option value="水果">水果</option>
              <option value="蔬菜">蔬菜</option>
              <option value="粮油">粮油</option>
              <option value="种子化肥">种子化肥</option>
              <option value="生鲜通用">生鲜通用</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">产地</label>
            <input v-model="form.origin" class="form-input" placeholder="例如：江西赣州" />
          </div>
          <div class="form-group">
            <label class="form-label">规格</label>
            <input v-model="form.specification" class="form-input" placeholder="例如：5斤装" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">定价</label>
            <input v-model="form.price" class="form-input" placeholder="例如：29.9元/5斤" />
          </div>
          <div class="form-group">
            <label class="form-label">目标平台</label>
            <select v-model="form.platform" class="form-select">
              <option value="douyin">抖音小店</option>
              <option value="pinduoduo">拼多多</option>
              <option value="huinong">惠农网</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">核心卖点（可选）</label>
          <input v-model="form.core_features" class="form-input" placeholder="例如：高糖度，皮薄汁多" />
        </div>

        <button
          class="btn btn-primary run-btn"
          @click="run"
          :disabled="loading || !form.product_name || !form.category"
        >
          <span v-if="loading" class="loading-spinner"></span>
          <span v-if="loading">AI全流程运行中（约30-60秒）...</span>
          <span v-else">⚡ 一键启动全流程</span>
        </button>
      </div>

      <!-- 流程进度（loading时展示） -->
      <div class="card progress-card" v-if="loading">
        <div class="progress-steps">
          <div :class="['step', { done: stage >= 1, active: stage === 0 }]">
            <span class="step-icon">{{ stage >= 1 ? '✅' : stage === 0 ? '⏳' : '⭕' }}</span>
            <span>痛点挖掘</span>
          </div>
          <div class="step-arrow">→</div>
          <div :class="['step', { done: stage >= 2, active: stage === 1 }]">
            <span class="step-icon">{{ stage >= 2 ? '✅' : stage === 1 ? '⏳' : '⭕' }}</span>
            <span>Listing生成</span>
          </div>
          <div class="step-arrow">→</div>
          <div :class="['step', { done: stage >= 3, active: stage === 2 }]">
            <span class="step-icon">{{ stage >= 3 ? '✅' : stage === 2 ? '⏳' : '⭕' }}</span>
            <span>合规校验</span>
          </div>
        </div>
        <p class="progress-tip">{{ progressTip }}</p>
      </div>

      <!-- 结果 -->
      <template v-if="result && !loading">
        <!-- 阶段状态 -->
        <div class="card stages-card">
          <div class="stages-row">
            <div
              v-for="s in stageItems"
              :key="s.key"
              :class="['stage-item', result.stages_completed.includes(s.key) ? 'done' : 'failed']"
            >
              <span>{{ result.stages_completed.includes(s.key) ? '✅' : '❌' }}</span>
              <span>{{ s.label }}</span>
            </div>
            <button class="btn btn-secondary reset-btn" @click="resetForm">重新分析</button>
          </div>
        </div>

        <!-- 左右布局：痛点 + Listing -->
        <div class="result-grid">
          <!-- 痛点报告 -->
          <div class="card pain-card">
            <h3 class="card-title">🔍 痛点分析</h3>
            <p class="summary-text">{{ result.pain_analysis.summary }}</p>
            <div class="pain-list">
              <div
                v-for="(pp, i) in result.pain_analysis.top_pain_points.slice(0, 5)"
                :key="i"
                class="pain-item"
              >
                <span class="pain-rank">{{ pp.rank || i+1 }}</span>
                <div>
                  <div class="pain-title">{{ pp.category }}</div>
                  <div class="pain-desc">{{ pp.pain_point }}</div>
                  <div class="pain-opp" v-if="pp.opportunity">💡 {{ pp.opportunity }}</div>
                </div>
              </div>
            </div>
            <div class="kw-section" v-if="result.pain_analysis.keyword_opportunities?.length">
              <div class="kw-label">关键词机会</div>
              <div class="kw-tags">
                <span class="kw-tag" v-for="kw in result.pain_analysis.keyword_opportunities" :key="kw">{{ kw }}</span>
              </div>
            </div>
          </div>

          <!-- Listing核心内容 -->
          <div class="card listing-card">
            <h3 class="card-title">✍️ 生成Listing</h3>

            <div class="rs">
              <div class="rs-top"><span class="rs-label">📌 标题</span><button class="btn-copy" @click="copy(result.listing.title)">复制</button></div>
              <div class="rs-title">{{ result.listing.title }}</div>
            </div>

            <div class="rs" v-if="result.listing.selling_points?.length">
              <div class="rs-top"><span class="rs-label">⭐ 卖点</span><button class="btn-copy" @click="copy(result.listing.selling_points.join('\n'))">复制</button></div>
              <ul class="sp-list">
                <li v-for="(sp, i) in result.listing.selling_points" :key="i">{{ sp }}</li>
              </ul>
            </div>

            <div class="rs" v-if="result.listing.video_script?.full_script">
              <div class="rs-top"><span class="rs-label">🎬 30秒口播</span><button class="btn-copy" @click="copy(result.listing.video_script.full_script)">复制</button></div>
              <div class="rs-content">{{ result.listing.video_script.full_script }}</div>
            </div>

            <!-- 合规状态 -->
            <div :class="['compliance-badge', result.compliance?.passed ? 'pass' : 'fail']" v-if="result.compliance">
              {{ result.compliance.passed ? '✅ 合规通过' : '⚠️ 有违规，已自动修复' }}
              <span class="c-detail">
                严重{{ result.compliance.critical_count }} | 警告{{ result.compliance.warning_count }}
              </span>
            </div>

            <div class="more-link">
              <router-link
                :to="{ path: '/listing', query: { product_name: result.product_name, category: result.category } }"
                class="btn btn-secondary"
              >查看完整Listing（含直播话术）→</router-link>
            </div>
          </div>
        </div>

        <!-- 快赢动作 -->
        <div class="card" v-if="result.pain_analysis.quick_wins?.length">
          <h3 class="card-title">⚡ 3天快赢动作</h3>
          <div class="quick-wins">
            <div class="qw-item" v-for="(qw, i) in result.pain_analysis.quick_wins" :key="i">
              <span class="qw-num">{{ i+1 }}</span>{{ qw }}
            </div>
          </div>
        </div>
      </template>

      <!-- 错误 -->
      <div class="card empty-state" v-if="!loading && !result">
        <span class="empty-icon">⚡</span>
        <p>填写产品信息后，点击"一键启动全流程"</p>
      </div>
    </div>

    <div class="error-toast" v-if="error">
      ⚠️ {{ error }}
      <button @click="error=''" style="margin-left:8px;background:none;border:none;cursor:pointer">×</button>
    </div>
    <div class="copy-toast" v-if="copyToast">✅ 已复制</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 120000 })

const form = ref({
  product_name: '', category: '', origin: '', specification: '',
  price: '', core_features: '', platform: 'douyin',
  sales_level: '中等（月销1000-5000单）', competitor_info: '',
})
const loading = ref(false)
const result = ref(null)
const error = ref('')
const copyToast = ref(false)
const stage = ref(0)

const stageItems = [
  { key: 'pain_point', label: '痛点挖掘' },
  { key: 'listing', label: 'Listing生成' },
]

const tips = ['正在分析市场痛点...', '正在生成Listing内容...', '正在进行合规校验...']
const progressTip = computed(() => tips[stage.value] || '处理中...')

let stageTimer = null

const run = async () => {
  loading.value = true
  error.value = ''
  result.value = null
  stage.value = 0

  stageTimer = setInterval(() => {
    stage.value = Math.min(stage.value + 1, 2)
  }, 8000)

  try {
    const token = localStorage.getItem('fc_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await http.post('/pipeline/run', form.value, { headers })
    if (res.data.code === 0) {
      result.value = res.data.data
      stage.value = 3
    } else {
      error.value = res.data.message || '执行失败'
    }
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '请求失败'
  } finally {
    clearInterval(stageTimer)
    loading.value = false
  }
}

const resetForm = () => { result.value = null; stage.value = 0 }

const copy = async (text) => {
  if (!text) return
  await navigator.clipboard.writeText(text).catch(() => {})
  copyToast.value = true
  setTimeout(() => { copyToast.value = false }, 2000)
}
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; display: flex; flex-direction: column; gap: 16px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.card-title { font-size: 15px; font-weight: 700; margin-bottom: 14px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.run-btn { width: 100%; margin-top: 8px; padding: 14px; font-size: 16px; }

/* Progress */
.progress-card { text-align: center; }
.progress-steps { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 12px; }
.step { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; }
.step.done { color: var(--green-dark); }
.step.active { color: var(--orange-primary); }
.step-arrow { color: var(--text-muted); font-size: 18px; }
.step-icon { font-size: 18px; }
.progress-tip { color: var(--text-muted); font-size: 13px; animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }

/* Stages */
.stages-card {}
.stages-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.stage-item { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; }
.stage-item.done { color: var(--green-dark); }
.stage-item.failed { color: #dc2626; }
.reset-btn { margin-left: auto; }

/* Result grid */
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.summary-text { font-size: 13px; color: var(--text-muted); margin-bottom: 12px; line-height: 1.6; }
.pain-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.pain-item { display: flex; gap: 10px; align-items: flex-start; }
.pain-rank {
  width: 24px; height: 24px; background: var(--green-primary); color: #fff;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.pain-title { font-size: 12px; font-weight: 700; color: var(--text-muted); }
.pain-desc { font-size: 13px; }
.pain-opp { font-size: 12px; color: var(--green-dark); margin-top: 2px; }
.kw-section { margin-top: 8px; }
.kw-label { font-size: 12px; font-weight: 600; margin-bottom: 6px; color: var(--text-muted); }
.kw-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.kw-tag { background: var(--green-light); color: var(--green-dark); padding: 3px 8px; border-radius: 5px; font-size: 12px; }

.rs { margin-bottom: 14px; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.rs-top { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f9fafb; border-bottom: 1px solid var(--border); }
.rs-label { font-size: 12px; font-weight: 700; }
.btn-copy { font-size: 11px; padding: 2px 8px; border: 1px solid var(--border); border-radius: 4px; background: #fff; cursor: pointer; }
.rs-title { padding: 10px 12px; font-size: 15px; font-weight: 700; line-height: 1.5; }
.sp-list { list-style: none; padding: 8px 12px; display: flex; flex-direction: column; gap: 5px; font-size: 12px; line-height: 1.6; }
.rs-content { padding: 10px 12px; font-size: 12px; line-height: 1.7; white-space: pre-wrap; background: #fafafa; }
.compliance-badge { padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.compliance-badge.pass { background: var(--green-bg); color: var(--green-dark); }
.compliance-badge.fail { background: #fffbeb; color: #b45309; }
.c-detail { font-weight: 400; color: var(--text-muted); font-size: 11px; }
.more-link { margin-top: 8px; }

/* Quick wins */
.quick-wins { display: flex; flex-direction: column; gap: 8px; }
.qw-item { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; }
.qw-num { width: 22px; height: 22px; background: var(--orange-primary); color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }

/* Toasts */
.copy-toast, .error-toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  padding: 10px 20px; border-radius: 8px; font-size: 13px; z-index: 999; box-shadow: var(--shadow-md);
}
.copy-toast { background: #f0fdf4; border: 1px solid var(--green-light); color: var(--green-dark); font-weight: 600; }
.error-toast { background: #fef2f2; border: 1px solid #fca5a5; color: #dc2626; }
</style>
