<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">💬 差评 / 售后话术</h1>
      <p class="page-desc">粘贴评论，AI自动识别类型（差评/催单/砍价/好评）并生成场景化回复，可直接发出</p>
    </div>

    <div class="page-body">
      <!-- 产品信息栏 -->
      <div class="card product-bar">
        <div class="pb-row">
          <div class="form-group">
            <label class="form-label">产品名称 <span class="req">*</span></label>
            <input v-model="productInfo.product_name" class="form-input" placeholder="例：赣南脐橙" />
          </div>
          <div class="form-group">
            <label class="form-label">产地</label>
            <input v-model="productInfo.origin" class="form-input" placeholder="例：江西赣州" />
          </div>
          <div class="form-group">
            <label class="form-label">价格</label>
            <input v-model="productInfo.price" class="form-input" placeholder="例：29.9元/5斤" />
          </div>
        </div>
      </div>

      <div class="main-layout">
        <!-- 左：输入区 -->
        <div class="input-col">
          <!-- 单条回复 -->
          <div class="card">
            <h3 class="card-title">单条评论回复</h3>
            <textarea v-model="singleComment" class="comment-input" placeholder="粘贴评论内容..." rows="4"></textarea>
            <button class="btn btn-primary w-full" @click="generateSingle" :disabled="singleLoading || !productInfo.product_name || !singleComment">
              <span v-if="singleLoading" class="loading-spinner"></span>
              {{ singleLoading ? 'AI生成中...' : '生成回复' }}
            </button>

            <!-- 单条结果 -->
            <div class="single-result" v-if="singleResult">
              <div class="result-meta">
                <span :class="['type-badge', `type-${typeColor(singleResult.comment_type)}`]">{{ singleResult.comment_type }}</span>
                <span :class="['urg-badge', `urg-${singleResult.urgency}`]">{{ singleResult.urgency }}优先</span>
                <span v-if="singleResult.risk_level === '高风险'" class="risk-badge">⚠️ 高风险</span>
              </div>
              <div class="reply-full">
                <div class="rl">完整回复</div>
                <div class="reply-text">{{ singleResult.reply }}</div>
                <button class="btn-copy-sm" @click="copy(singleResult.reply)">复制</button>
              </div>
              <div class="reply-short-box">
                <div class="rl">简短版（30字内）</div>
                <div class="reply-text short">{{ singleResult.reply_short }}</div>
                <button class="btn-copy-sm" @click="copy(singleResult.reply_short)">复制</button>
              </div>
              <div class="followup" v-if="singleResult.follow_up_action && singleResult.follow_up_action !== '无需跟进'">
                📌 跟进：{{ singleResult.follow_up_action }}
              </div>
              <div class="feedback-row" v-if="!feedbackDone['single']">
                <span class="fb-label">这条回复：</span>
                <button class="fb-btn usable" @click="submitFeedback('single', 'usable', singleResult.reply)">✅ 直接可用</button>
                <button class="fb-btn edit" @click="submitFeedback('single', 'needs_edit', singleResult.reply)">✏️ 改了能用</button>
                <button class="fb-btn bad" @click="submitFeedback('single', 'unusable', '')">❌ 不能用</button>
              </div>
              <div class="fb-done" v-else>✅ 反馈已记录</div>
            </div>
          </div>

          <!-- 批量回复 -->
          <div class="card">
            <h3 class="card-title">批量评论回复（最多20条）</h3>
            <div class="batch-tip">每行一条评论，粘贴后点击生成</div>
            <textarea v-model="batchText" class="comment-input" rows="8" placeholder="好甜啊！&#10;啥时候发货&#10;能便宜点吗&#10;收到了，包装不错"></textarea>
            <button class="btn btn-secondary w-full" @click="generateBatch" :disabled="batchLoading || !productInfo.product_name || !batchText">
              <span v-if="batchLoading" class="loading-spinner"></span>
              {{ batchLoading ? 'AI批量生成中...' : '批量生成回复' }}
            </button>
          </div>
        </div>

        <!-- 右：批量结果 -->
        <div class="result-col">
          <div class="card" v-if="batchResults.length">
            <div class="card-title-row">
              <h3 class="card-title">批量回复结果（{{ batchResults.length }}条）</h3>
              <button class="btn btn-secondary" @click="copyAll">一键复制全部</button>
            </div>
            <div class="batch-list">
              <div v-for="(item, i) in batchResults" :key="i" :class="['batch-item', item.urgency === '高' ? 'urgent' : '']">
                <div class="bi-original">「{{ item.original_comment }}」</div>
                <div class="bi-meta">
                  <span :class="['type-badge', `type-${typeColor(item.comment_type)}`]">{{ item.comment_type }}</span>
                  <span v-if="item.risk_level === '高风险'" class="risk-badge">⚠️</span>
                </div>
                <div class="bi-reply">{{ item.reply_short }}</div>
                <div class="bi-actions">
                  <button class="btn-copy-sm" @click="copy(item.reply)">复制完整版</button>
                  <button class="btn-copy-sm" @click="copy(item.reply_short)">复制简短版</button>
                </div>
                <div class="bi-followup" v-if="item.follow_up_action && item.follow_up_action !== '无需跟进'">
                  📌 {{ item.follow_up_action }}
                </div>
              </div>
            </div>
          </div>

          <div class="card empty-state" v-else>
            <span class="empty-icon">💬</span>
            <p>批量回复结果显示在这里</p>
            <div class="type-legend">
              <div v-for="t in typeLegend" :key="t.type" :class="['leg-item', `type-${t.color}`]">{{ t.type }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="copy-toast" v-if="copyToast">✅ 已复制</div>
    <div class="error-msg" v-if="errorMsg">⚠️ {{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { replyApi, feedbackApi } from '../api/index.js'

const productInfo = ref({ product_name: '', origin: '', price: '' })
const singleComment = ref('')
const batchText = ref('')
const singleLoading = ref(false)
const batchLoading = ref(false)
const singleResult = ref(null)
const batchResults = ref([])
const copyToast = ref(false)
const errorMsg = ref('')
const feedbackDone = ref({})

const typeColorMap = { '好评': 'green', '差评': 'red', '质量投诉': 'red', '发货催单': 'orange', '价格询问': 'blue', '砍价': 'orange', '产品咨询': 'blue', '其他': 'gray' }
const typeColor = (t) => typeColorMap[t] || 'gray'

const typeLegend = [
  { type: '好评', color: 'green' }, { type: '差评/投诉', color: 'red' },
  { type: '催单/砍价', color: 'orange' }, { type: '咨询', color: 'blue' },
]

const generateSingle = async () => {
  singleLoading.value = true
  errorMsg.value = ''
  singleResult.value = null
  try {
    const res = await replyApi.generate({ ...productInfo.value, comment: singleComment.value })
    if (res.code === 0) singleResult.value = res.data
    else errorMsg.value = res.message
  } catch (e) { errorMsg.value = e.message }
  finally { singleLoading.value = false }
}

const generateBatch = async () => {
  batchLoading.value = true
  errorMsg.value = ''
  batchResults.value = []
  const comments = batchText.value.split('\n').map(s => s.trim()).filter(Boolean).slice(0, 20)
  if (!comments.length) { batchLoading.value = false; return }
  try {
    const res = await replyApi.batch({ ...productInfo.value, comments })
    if (res.code === 0) batchResults.value = res.data
    else errorMsg.value = res.message
  } catch (e) { errorMsg.value = e.message }
  finally { batchLoading.value = false }
}

const copy = async (text) => {
  if (!text) return
  await navigator.clipboard.writeText(text).catch(() => {})
  copyToast.value = true
  setTimeout(() => copyToast.value = false, 2000)
}

const copyAll = async () => {
  const text = batchResults.value.map((r, i) =>
    `${i+1}. 原评论：${r.original_comment}\n   回复：${r.reply_short}`
  ).join('\n\n')
  await copy(text)
}

const submitFeedback = async (key, rating, text) => {
  feedbackDone.value[key] = true
  try {
    await feedbackApi.submit({
      content_type: 'reply',
      content_id: key,
      product_name: productInfo.value.product_name,
      category: '通用',
      rating,
      edited_text: rating === 'usable' ? text : '',
      comment: '',
    })
  } catch {}
}
</script>

<style scoped>
.page { min-height:100vh; }
.page-body { padding:0 32px 32px; display:flex; flex-direction:column; gap:14px; }
.card { background:#fff; border-radius:12px; padding:20px; border:1px solid var(--border); }
.card-title { font-size:15px; font-weight:700; margin-bottom:12px; }
.card-title-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }

.product-bar .pb-row { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }
.req { color:#ef4444; }
.w-full { width:100%; margin-top:8px; }
.comment-input { width:100%; border:1px solid var(--border); border-radius:8px; padding:10px; font-size:13px; resize:vertical; font-family:inherit; margin-bottom:10px; }
.batch-tip { font-size:12px; color:var(--text-muted); margin-bottom:8px; }

.main-layout { display:grid; grid-template-columns:1fr 1fr; gap:16px; align-items:start; }
.input-col, .result-col { display:flex; flex-direction:column; gap:14px; }

/* Single result */
.single-result { margin-top:14px; border-top:1px solid var(--border); padding-top:14px; display:flex; flex-direction:column; gap:10px; }
.result-meta { display:flex; gap:8px; align-items:center; }
.rl { font-size:11px; font-weight:700; color:var(--text-muted); margin-bottom:5px; }
.reply-full, .reply-short-box { background:#f9fafb; border-radius:8px; padding:12px; position:relative; }
.reply-text { font-size:13px; line-height:1.7; margin-bottom:8px; }
.reply-text.short { color:var(--green-dark); font-weight:600; }
.followup { font-size:12px; color:#c2410c; background:var(--orange-light); padding:8px 12px; border-radius:6px; }

/* Badges */
.type-badge { font-size:11px; font-weight:700; padding:2px 8px; border-radius:4px; }
.type-green { background:var(--green-bg); color:var(--green-dark); }
.type-red { background:#fef2f2; color:#dc2626; }
.type-orange { background:var(--orange-light); color:#c2410c; }
.type-blue { background:#eff6ff; color:#1d4ed8; }
.type-gray { background:#f3f4f6; color:var(--text-muted); }
.urg-badge { font-size:10px; padding:2px 6px; border-radius:4px; }
.urg-高 { background:#fef2f2; color:#dc2626; }
.urg-中 { background:#fffbeb; color:#92400e; }
.urg-低 { background:#f3f4f6; color:var(--text-muted); }
.risk-badge { font-size:11px; color:#dc2626; font-weight:700; }

/* Batch */
.batch-list { display:flex; flex-direction:column; gap:10px; }
.batch-item { border:1px solid var(--border); border-radius:8px; padding:12px; }
.batch-item.urgent { border-color:#fca5a5; background:#fef2f2; }
.bi-original { font-size:12px; color:var(--text-muted); margin-bottom:6px; }
.bi-meta { display:flex; gap:6px; margin-bottom:6px; }
.bi-reply { font-size:13px; font-weight:600; color:var(--text); margin-bottom:8px; line-height:1.5; }
.bi-actions { display:flex; gap:6px; margin-bottom:6px; }
.bi-followup { font-size:11px; color:#c2410c; }

/* Legend */
.type-legend { display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; justify-content:center; }
.leg-item { font-size:12px; font-weight:700; padding:4px 10px; border-radius:4px; }

/* Empty */
.empty-state { text-align:center; padding:60px 20px; }
.empty-icon { font-size:48px; display:block; margin-bottom:12px; }
.empty-state p { color:var(--text-muted); font-size:14px; }

.btn-copy-sm { font-size:11px; padding:4px 10px; border:1px solid var(--border); border-radius:6px; background:#fff; cursor:pointer; color:var(--text-muted); }

.feedback-row { display:flex; align-items:center; gap:6px; margin-top:10px; padding-top:10px; border-top:1px solid var(--border); flex-wrap:wrap; }
.fb-label { font-size:12px; color:var(--text-muted); }
.fb-btn { font-size:11px; padding:4px 10px; border-radius:6px; border:1px solid; cursor:pointer; font-weight:600; }
.fb-btn.usable { border-color:var(--green-light); color:var(--green-dark); background:var(--green-bg); }
.fb-btn.edit { border-color:#fde68a; color:#92400e; background:#fffbeb; }
.fb-btn.bad { border-color:#fca5a5; color:#dc2626; background:#fef2f2; }
.fb-done { font-size:12px; color:var(--green-dark); margin-top:8px; }

.copy-toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:#f0fdf4; border:1px solid var(--green-light); color:var(--green-dark); padding:10px 20px; border-radius:8px; font-size:13px; z-index:999; }
.error-msg { position:fixed; bottom:64px; left:50%; transform:translateX(-50%); background:#fef2f2; border:1px solid #fca5a5; color:#dc2626; padding:10px 20px; border-radius:8px; font-size:13px; z-index:999; white-space:nowrap; max-width:400px; }
</style>
