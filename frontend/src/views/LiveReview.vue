<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">🔴 直播复盘</h1>
      <p class="page-desc">输入今场数据，AI诊断问题 + 给出下场改进方案</p>
    </div>

    <div class="page-body">
      <div class="layout">
        <!-- 左：输入表单 -->
        <div class="form-col">
          <div class="card">
            <h3 class="card-title">今场数据</h3>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">品类 <span class="req">*</span></label>
                <select v-model="form.category" class="form-select">
                  <option value="">选择品类</option>
                  <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">主推产品 <span class="req">*</span></label>
                <input v-model="form.product_name" class="form-input" placeholder="例：赣南脐橙" />
              </div>
            </div>

            <div class="form-section-label">📊 核心数据</div>
            <div class="form-row3">
              <div class="form-group">
                <label class="form-label">直播时长（分钟）</label>
                <input v-model.number="form.duration" type="number" class="form-input" placeholder="120" />
              </div>
              <div class="form-group">
                <label class="form-label">最高同时在线</label>
                <input v-model.number="form.peak_viewers" type="number" class="form-input" placeholder="0" />
              </div>
              <div class="form-group">
                <label class="form-label">平均在线人数</label>
                <input v-model.number="form.avg_viewers" type="number" class="form-input" placeholder="0" />
              </div>
              <div class="form-group">
                <label class="form-label">评论数</label>
                <input v-model.number="form.comments" type="number" class="form-input" placeholder="0" />
              </div>
              <div class="form-group">
                <label class="form-label">下单人数</label>
                <input v-model.number="form.orders" type="number" class="form-input" placeholder="0" />
              </div>
              <div class="form-group">
                <label class="form-label">成交金额（元）</label>
                <input v-model.number="form.gmv" type="number" class="form-input" placeholder="0" />
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">话术/节奏描述（选填）</label>
              <textarea v-model="form.script_notes" class="form-textarea" placeholder="例：开场说了5分钟才开始介绍产品，中间搞了一次抽奖..." rows="3"></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">你自己觉得哪里有问题？（选填）</label>
              <textarea v-model="form.merchant_notes" class="form-textarea" placeholder="例：感觉人一直在掉，下单的人太少..." rows="3"></textarea>
            </div>

            <button class="btn btn-primary w-full" @click="analyze" :disabled="loading || !form.category || !form.product_name">
              <span v-if="loading" class="loading-spinner"></span>
              {{ loading ? 'AI复盘分析中...' : '🔍 开始复盘分析' }}
            </button>
          </div>
        </div>

        <!-- 右：结果 -->
        <div class="result-col" v-if="result">
          <!-- 评分 -->
          <div class="card score-card">
            <div class="score-row">
              <div class="score-circle" :class="scoreClass">
                <span class="score-num">{{ result.overall_score }}</span>
                <span class="score-label">分</span>
              </div>
              <div class="score-info">
                <div class="score-title">本场直播评分</div>
                <div class="score-reason">{{ result.score_reason }}</div>
                <div class="score-highlight" v-if="result.highlight">⭐ {{ result.highlight }}</div>
              </div>
            </div>
          </div>

          <!-- 流量漏斗 -->
          <div class="card" v-if="result.funnel?.bottleneck">
            <h3 class="card-title">📉 流量漏斗分析</h3>
            <div class="funnel-bottleneck">⚠️ 最大漏点：{{ result.funnel.bottleneck }}</div>
            <div class="funnel-rows">
              <div class="funnel-row" v-for="(val, key) in funnelDisplay" :key="key">
                <span class="fl">{{ val.label }}</span>
                <span class="fv">{{ val.value }}</span>
              </div>
            </div>
          </div>

          <!-- 问题诊断 -->
          <div class="card" v-if="result.problems?.length">
            <h3 class="card-title">🚨 问题诊断</h3>
            <div class="problem-list">
              <div v-for="p in result.problems" :key="p.title" :class="['problem-item', `sev-${p.severity}`]">
                <div class="problem-header">
                  <span class="problem-type">{{ p.type }}</span>
                  <span class="problem-title">{{ p.title }}</span>
                  <span :class="['sev-badge', `sev-${p.severity}`]">{{ p.severity }}</span>
                </div>
                <div class="problem-desc">{{ p.desc }}</div>
              </div>
            </div>
          </div>

          <!-- 改进建议 -->
          <div class="card" v-if="result.improvements?.length">
            <h3 class="card-title">💡 改进建议</h3>
            <div class="improve-list">
              <div v-for="(imp, i) in result.improvements" :key="i" class="improve-item">
                <div class="improve-area">{{ imp.area }}</div>
                <div class="improve-action">{{ imp.action }}</div>
                <div class="improve-expected">🎯 {{ imp.expected }}</div>
              </div>
            </div>
          </div>

          <!-- 下场计划 -->
          <div class="card next-card" v-if="result.next_session_plan">
            <div class="card-title-row">
              <h3 class="card-title">📋 下场直播计划</h3>
              <button class="btn-copy-sm" @click="copyNextPlan">复制计划</button>
            </div>
            <div class="next-item"><span class="ni-label">关键任务</span><span class="ni-val highlight">{{ result.next_session_plan.key_focus }}</span></div>
            <div class="next-item"><span class="ni-label">开场前30秒</span><span class="ni-val script-text">{{ result.next_session_plan.opening_30s }}</span></div>
            <div class="next-item"><span class="ni-label">排品顺序</span><span class="ni-val">{{ result.next_session_plan.product_order }}</span></div>
            <div class="next-item"><span class="ni-label">时长/时段</span><span class="ni-val">{{ result.next_session_plan.timing }}</span></div>
          </div>

          <!-- 反馈 -->
          <div class="card feedback-bar" v-if="!feedbackDone">
            <span class="fb-label">这份复盘报告：</span>
            <button class="fb-btn usable" @click="submitFeedback('usable')">✅ 准确有用</button>
            <button class="fb-btn edit" @click="submitFeedback('needs_edit')">✏️ 部分有用</button>
            <button class="fb-btn bad" @click="submitFeedback('unusable')">❌ 不准确</button>
          </div>
          <div class="fb-done-text" v-else>✅ 反馈已记录，感谢！</div>
        </div>

        <!-- 右：空状态 -->
        <div class="result-col empty-col" v-else-if="!loading">
          <div class="card empty-state">
            <span class="empty-icon">📊</span>
            <p>填写左侧直播数据</p>
            <p>AI帮你诊断问题 + 给下场方案</p>
          </div>
        </div>
      </div>
    </div>

    <div class="copy-toast" v-if="copyToast">✅ 已复制</div>
    <div class="error-msg" v-if="errorMsg">⚠️ {{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { liveReviewApi, feedbackApi } from '../api/index.js'

const categories = ['脐橙', '苹果', '草莓', '樱桃', '蓝莓', '猕猴桃', '芒果', '桃子', '葡萄', '西瓜', '沃柑', '石榴', '蔬菜', '粮油']
const form = ref({
  category: '', product_name: '', duration: 120,
  peak_viewers: 0, avg_viewers: 0, comments: 0,
  likes: 0, orders: 0, gmv: 0, refund_rate: 0,
  script_notes: '', merchant_notes: '',
})
const loading = ref(false)
const result = ref(null)
const errorMsg = ref('')
const copyToast = ref(false)
const feedbackDone = ref(false)

const scoreClass = computed(() => {
  const s = result.value?.overall_score || 0
  if (s >= 80) return 'score-good'
  if (s >= 60) return 'score-mid'
  return 'score-low'
})

const funnelDisplay = computed(() => {
  if (!result.value?.funnel) return {}
  const f = result.value.funnel
  return {
    enter_to_stay: { label: '进场→停留', value: f.enter_to_stay },
    stay_to_interact: { label: '停留→互动', value: f.stay_to_interact },
    interact_to_order: { label: '互动→下单', value: f.interact_to_order },
  }
})

const analyze = async () => {
  loading.value = true
  errorMsg.value = ''
  result.value = null
  try {
    const res = await liveReviewApi.analyze(form.value)
    if (res.code === 0) result.value = res.data
    else errorMsg.value = res.message
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    loading.value = false
  }
}

const copyNextPlan = async () => {
  if (!result.value?.next_session_plan) return
  const p = result.value.next_session_plan
  const text = `下场直播计划\n\n关键任务：${p.key_focus}\n开场前30秒：${p.opening_30s}\n排品顺序：${p.product_order}\n时长/时段：${p.timing}`
  await navigator.clipboard.writeText(text).catch(() => {})
  copyToast.value = true
  setTimeout(() => copyToast.value = false, 2000)
}

const submitFeedback = async (rating) => {
  feedbackDone.value = true
  try {
    await feedbackApi.submit({
      content_type: 'live_review',
      content_id: 'report',
      product_name: form.value.product_name,
      category: form.value.category,
      rating,
      edited_text: '',
      comment: '',
    })
  } catch {}
}
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; }
.card { background:#fff; border-radius:12px; padding:20px; border:1px solid var(--border); margin-bottom:14px; }
.card-title { font-size:15px; font-weight:700; margin-bottom:14px; }
.card-title-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }

.layout { display:grid; grid-template-columns:400px 1fr; gap:20px; align-items:start; }
.form-col, .result-col { display:flex; flex-direction:column; }

.form-section-label { font-size:12px; font-weight:700; color:var(--text-muted); margin:12px 0 8px; text-transform:uppercase; }
.form-row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.form-row3 { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.form-textarea { width:100%; border:1px solid var(--border); border-radius:8px; padding:10px; font-size:13px; resize:vertical; font-family:inherit; }
.req { color:#ef4444; }
.w-full { width:100%; margin-top:8px; }

/* Score */
.score-card { }
.score-row { display:flex; align-items:center; gap:20px; }
.score-circle { width:80px; height:80px; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center; flex-shrink:0; }
.score-circle.score-good { background:var(--green-bg); border:3px solid var(--green-primary); }
.score-circle.score-mid { background:#fffbeb; border:3px solid #f59e0b; }
.score-circle.score-low { background:#fef2f2; border:3px solid #ef4444; }
.score-num { font-size:26px; font-weight:900; color:var(--text); line-height:1; }
.score-label { font-size:11px; color:var(--text-muted); }
.score-info { flex:1; }
.score-title { font-size:14px; font-weight:700; margin-bottom:6px; }
.score-reason { font-size:13px; color:var(--text-muted); line-height:1.6; }
.score-highlight { margin-top:8px; font-size:13px; color:var(--green-dark); font-weight:600; }

/* Funnel */
.funnel-bottleneck { background:#fef2f2; border:1px solid #fca5a5; color:#dc2626; font-size:13px; font-weight:600; padding:8px 12px; border-radius:8px; margin-bottom:10px; }
.funnel-rows { display:flex; flex-direction:column; gap:8px; }
.funnel-row { display:flex; gap:10px; font-size:13px; }
.fl { color:var(--text-muted); font-weight:600; width:90px; flex-shrink:0; }
.fv { flex:1; }

/* Problems */
.problem-list { display:flex; flex-direction:column; gap:8px; }
.problem-item { border-left:4px solid; border-radius:0 8px 8px 0; padding:10px 12px; }
.problem-item.sev-高 { border-color:#ef4444; background:#fef2f2; }
.problem-item.sev-中 { border-color:#f59e0b; background:#fffbeb; }
.problem-item.sev-低 { border-color:var(--green-primary); background:var(--green-bg); }
.problem-header { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
.problem-type { font-size:11px; background:#e5e7eb; padding:2px 6px; border-radius:4px; color:var(--text-muted); }
.problem-title { font-size:13px; font-weight:700; }
.sev-badge { font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; margin-left:auto; }
.sev-badge.sev-高 { background:#fca5a5; color:#991b1b; }
.sev-badge.sev-中 { background:#fde68a; color:#92400e; }
.sev-badge.sev-低 { background:var(--green-light); color:var(--green-dark); }
.problem-desc { font-size:12px; color:var(--text-muted); }

/* Improvements */
.improve-list { display:flex; flex-direction:column; gap:10px; }
.improve-item { background:#f9fafb; border-radius:8px; padding:12px; }
.improve-area { font-size:11px; font-weight:700; color:var(--green-dark); background:var(--green-bg); display:inline-block; padding:2px 8px; border-radius:4px; margin-bottom:6px; }
.improve-action { font-size:13px; line-height:1.6; margin-bottom:4px; }
.improve-expected { font-size:12px; color:var(--green-dark); font-weight:600; }

/* Next Plan */
.next-item { display:flex; gap:12px; padding:8px 0; border-bottom:1px solid var(--border); font-size:13px; }
.next-item:last-child { border-bottom:none; }
.ni-label { color:var(--text-muted); font-weight:700; width:90px; flex-shrink:0; font-size:12px; padding-top:2px; }
.ni-val { flex:1; line-height:1.6; }
.ni-val.highlight { color:var(--green-dark); font-weight:700; }
.ni-val.script-text { color:var(--orange-primary); font-weight:600; }

.empty-col { min-height:300px; }
.empty-state { text-align:center; padding:60px 20px; }
.empty-icon { font-size:48px; display:block; margin-bottom:12px; }
.empty-state p { color:var(--text-muted); font-size:14px; margin:4px 0; }

.btn-copy-sm { font-size:11px; padding:4px 10px; border:1px solid var(--border); border-radius:6px; background:#fff; cursor:pointer; }

.feedback-bar { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.fb-label { font-size:12px; color:var(--text-muted); }
.fb-btn { font-size:11px; padding:4px 10px; border-radius:6px; border:1px solid; cursor:pointer; font-weight:600; }
.fb-btn.usable { border-color:var(--green-light); color:var(--green-dark); background:var(--green-bg); }
.fb-btn.edit { border-color:#fde68a; color:#92400e; background:#fffbeb; }
.fb-btn.bad { border-color:#fca5a5; color:#dc2626; background:#fef2f2; }
.fb-done-text { font-size:12px; color:var(--green-dark); padding:10px 0; }

.copy-toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:#f0fdf4; border:1px solid var(--green-light); color:var(--green-dark); padding:10px 20px; border-radius:8px; font-size:13px; z-index:999; }
.error-msg { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:#fef2f2; border:1px solid #fca5a5; color:#dc2626; padding:10px 20px; border-radius:8px; font-size:13px; z-index:999; }
</style>
