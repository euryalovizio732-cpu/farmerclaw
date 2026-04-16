<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">🚀 投放优化</h1>
      <p class="page-desc">输入视频数据，AI判断是否值得投DOU+ + 给出时段/人群/预算方案</p>
    </div>

    <div class="page-body">
      <div class="layout">
        <!-- 左：表单 -->
        <div class="form-col">
          <div class="card">
            <h3 class="card-title">产品 & 视频信息</h3>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">品类 <span class="req">*</span></label>
                <select v-model="form.category" class="form-select">
                  <option value="">选择品类</option>
                  <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">产品名称 <span class="req">*</span></label>
                <input v-model="form.product_name" class="form-input" placeholder="例：赣南脐橙" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">视频类型</label>
                <select v-model="form.video_type" class="form-select">
                  <option v-for="t in videoTypes" :key="t" :value="t">{{ t }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">视频时长（秒）</label>
                <input v-model.number="form.duration" type="number" class="form-input" placeholder="30" />
              </div>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title">📊 视频数据（发布后查看）</h3>
            <div class="form-row3">
              <div class="form-group">
                <label class="form-label">自然播放量</label>
                <input v-model.number="form.natural_views" type="number" class="form-input" placeholder="0" />
              </div>
              <div class="form-group">
                <label class="form-label">完播率（%）</label>
                <input v-model.number="form.completion_rate" type="number" step="0.1" class="form-input" placeholder="0.0" />
              </div>
              <div class="form-group">
                <label class="form-label">点赞率（%）</label>
                <input v-model.number="form.like_rate" type="number" step="0.1" class="form-input" placeholder="0.0" />
              </div>
              <div class="form-group">
                <label class="form-label">评论率（%）</label>
                <input v-model.number="form.comment_rate" type="number" step="0.1" class="form-input" placeholder="0.0" />
              </div>
              <div class="form-group">
                <label class="form-label">账号粉丝数</label>
                <input v-model.number="form.followers" type="number" class="form-input" placeholder="0" />
              </div>
              <div class="form-group">
                <label class="form-label">历史均播</label>
                <input v-model.number="form.avg_views" type="number" class="form-input" placeholder="0" />
              </div>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title">💰 预算设置</h3>
            <div class="budget-options">
              <button v-for="b in budgetOptions" :key="b" :class="['budget-btn', form.budget===b?'active':'']" @click="form.budget=b">
                {{ b }}元
              </button>
              <input v-model.number="form.budget" type="number" class="form-input budget-custom" placeholder="自定义" />
            </div>
          </div>

          <button class="btn btn-primary w-full" @click="optimize" :disabled="loading || !form.category || !form.product_name">
            <span v-if="loading" class="loading-spinner"></span>
            {{ loading ? 'AI分析中...' : '🚀 获取投放建议' }}
          </button>
        </div>

        <!-- 右：结果 -->
        <div class="result-col" v-if="result">
          <!-- 投放判断 -->
          <div :class="['card', 'boost-card', result.should_boost ? 'should-boost' : 'no-boost']">
            <div class="boost-row">
              <div class="boost-icon">{{ result.should_boost ? '✅' : '⚠️' }}</div>
              <div class="boost-info">
                <div class="boost-title">{{ result.should_boost ? '建议投放 DOU+' : '暂不建议投放' }}</div>
                <div class="boost-reason">{{ result.should_boost_reason }}</div>
              </div>
              <div class="boost-score">
                <span class="score-num">{{ result.score }}</span>
                <span class="score-unit">分</span>
              </div>
            </div>
          </div>

          <!-- 评分明细 -->
          <div class="card" v-if="result.score_breakdown">
            <h3 class="card-title">评分明细</h3>
            <div class="score-items">
              <div v-for="(val, key) in result.score_breakdown" :key="key" class="score-item">
                <span class="si-label">{{ scoreLabels[key] || key }}</span>
                <span class="si-val">{{ val }}</span>
              </div>
            </div>
          </div>

          <!-- 时段建议 -->
          <div class="card" v-if="result.timing">
            <h3 class="card-title">⏰ 最佳投放时段</h3>
            <div class="timing-hours">
              <span v-for="h in result.timing.best_hours" :key="h" class="hour-tag">{{ h }}</span>
            </div>
            <div class="timing-days">{{ result.timing.best_days }}</div>
            <div class="timing-reason">{{ result.timing.reason }}</div>
          </div>

          <!-- 人群定向 -->
          <div class="card" v-if="result.target_audience">
            <h3 class="card-title">🎯 人群定向建议</h3>
            <div class="audience-grid">
              <div class="aud-item"><span class="al">性别</span><span>{{ result.target_audience.gender }}</span></div>
              <div class="aud-item"><span class="al">年龄</span><span>{{ result.target_audience.age }}</span></div>
              <div class="aud-item"><span class="al">地域</span><span>{{ result.target_audience.region }}</span></div>
              <div class="aud-item full"><span class="al">兴趣标签</span>
                <span class="int-tags">
                  <span v-for="tag in result.target_audience.interest" :key="tag" class="int-tag">{{ tag }}</span>
                </span>
              </div>
              <div class="aud-item full"><span class="al">选择原因</span><span>{{ result.target_audience.reason }}</span></div>
            </div>
          </div>

          <!-- 预算计划 -->
          <div class="card" v-if="result.budget_plan">
            <h3 class="card-title">💰 预算分配计划</h3>
            <div class="budget-plan">
              <div class="bp-item"><span class="bl">第一阶段</span><span>{{ result.budget_plan.phase1 }}</span></div>
              <div class="bp-item"><span class="bl">第二阶段</span><span>{{ result.budget_plan.phase2 }}</span></div>
              <div class="bp-item stop"><span class="bl">停投信号</span><span>{{ result.budget_plan.stop_signal }}</span></div>
            </div>
          </div>

          <!-- 置顶话术 -->
          <div class="card" v-if="result.copy_suggestion">
            <div class="card-title-row">
              <h3 class="card-title">📌 评论区置顶话术</h3>
              <button class="btn-copy-sm" @click="copy(result.copy_suggestion)">复制</button>
            </div>
            <div class="copy-text">{{ result.copy_suggestion }}</div>
          </div>

          <!-- 投放目标 & 风险 -->
          <div class="card risk-card" v-if="result.objective || result.risk">
            <div class="obj-row" v-if="result.objective"><span class="ol">投放目标</span><span>{{ result.objective }}</span></div>
            <div class="risk-row" v-if="result.risk"><span class="rl">风险提示</span><span>{{ result.risk }}</span></div>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="result-col empty-col" v-else-if="!loading">
          <div class="card empty-state">
            <span class="empty-icon">🚀</span>
            <p>填写视频数据，AI帮你决定</p>
            <p>这条视频值不值得花钱投</p>
            <div class="threshold-tips">
              <div class="tt">完播率 ≥ 35% → 值得投</div>
              <div class="tt">自然播放 ≥ 500 → 有基础</div>
              <div class="tt">评论率 ≥ 1% → 有互动</div>
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
import { adApi } from '../api/index.js'

const categories = ['水果', '蔬菜', '粮油', '种子化肥', '生鲜通用']
const videoTypes = ['口播', '产地探访', '对比测评', '知识科普', '情感故事']
const budgetOptions = [100, 200, 300, 500]

const form = ref({
  category: '', product_name: '', origin: '', price: '',
  video_type: '口播', natural_views: 0, completion_rate: 0,
  like_rate: 0, comment_rate: 0, share_rate: 0,
  duration: 30, publish_time: '', followers: 0, avg_views: 0,
  has_violation: '无', budget: 300,
})

const loading = ref(false)
const result = ref(null)
const copyToast = ref(false)
const errorMsg = ref('')

const scoreLabels = {
  completion_score: '完播率',
  engagement_score: '互动率',
  content_score: '内容质量',
}

const optimize = async () => {
  loading.value = true
  errorMsg.value = ''
  result.value = null
  try {
    const res = await adApi.optimize(form.value)
    if (res.code === 0) result.value = res.data
    else errorMsg.value = res.message
  } catch (e) { errorMsg.value = e.message }
  finally { loading.value = false }
}

const copy = async (text) => {
  if (!text) return
  await navigator.clipboard.writeText(text).catch(() => {})
  copyToast.value = true
  setTimeout(() => copyToast.value = false, 2000)
}
</script>

<style scoped>
.page { min-height:100vh; }
.page-body { padding:0 32px 32px; }
.card { background:#fff; border-radius:12px; padding:20px; border:1px solid var(--border); margin-bottom:14px; }
.card-title { font-size:15px; font-weight:700; margin-bottom:14px; }
.card-title-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }

.layout { display:grid; grid-template-columns:380px 1fr; gap:20px; align-items:start; }
.form-col, .result-col { display:flex; flex-direction:column; }
.form-row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.form-row3 { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.req { color:#ef4444; }
.w-full { width:100%; }

/* Budget */
.budget-options { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.budget-btn { padding:6px 14px; border:1px solid var(--border); border-radius:6px; background:#fff; font-size:13px; font-weight:600; cursor:pointer; color:var(--text-muted); }
.budget-btn.active { background:var(--green-primary); color:#fff; border-color:var(--green-primary); }
.budget-custom { width:90px !important; }

/* Boost card */
.boost-card { }
.boost-card.should-boost { border-color:var(--green-primary); background:var(--green-bg); }
.boost-card.no-boost { border-color:#f59e0b; background:#fffbeb; }
.boost-row { display:flex; align-items:center; gap:14px; }
.boost-icon { font-size:32px; }
.boost-info { flex:1; }
.boost-title { font-size:16px; font-weight:800; margin-bottom:4px; }
.boost-reason { font-size:13px; color:var(--text-muted); line-height:1.5; }
.boost-score { text-align:center; }
.score-num { font-size:32px; font-weight:900; }
.score-unit { font-size:12px; color:var(--text-muted); }

/* Score breakdown */
.score-items { display:flex; flex-direction:column; gap:8px; }
.score-item { display:flex; gap:12px; font-size:13px; padding:8px 0; border-bottom:1px solid var(--border); }
.score-item:last-child { border-bottom:none; }
.si-label { font-weight:700; width:80px; flex-shrink:0; }
.si-val { flex:1; color:var(--text-muted); }

/* Timing */
.timing-hours { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px; }
.hour-tag { background:var(--green-primary); color:#fff; font-size:13px; font-weight:700; padding:4px 12px; border-radius:6px; }
.timing-days { font-size:13px; font-weight:600; margin-bottom:4px; }
.timing-reason { font-size:12px; color:var(--text-muted); }

/* Audience */
.audience-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.aud-item { display:flex; gap:8px; font-size:13px; align-items:flex-start; }
.aud-item.full { grid-column:1/-1; }
.al { color:var(--text-muted); font-weight:700; width:70px; flex-shrink:0; font-size:12px; }
.int-tags { display:flex; gap:5px; flex-wrap:wrap; }
.int-tag { background:var(--green-bg); color:var(--green-dark); font-size:11px; padding:2px 8px; border-radius:4px; }

/* Budget plan */
.budget-plan { display:flex; flex-direction:column; gap:8px; }
.bp-item { display:flex; gap:12px; font-size:13px; padding:8px 10px; background:#f9fafb; border-radius:6px; }
.bp-item.stop { background:#fef2f2; }
.bl { font-weight:700; width:70px; flex-shrink:0; }

/* Copy text */
.copy-text { font-size:13px; line-height:1.7; background:#f9fafb; padding:12px; border-radius:8px; font-weight:600; color:var(--green-dark); }

/* Risk */
.risk-card { }
.obj-row, .risk-row { display:flex; gap:12px; font-size:13px; padding:6px 0; }
.ol { font-weight:700; color:var(--green-dark); width:70px; flex-shrink:0; }
.rl { font-weight:700; color:#c2410c; width:70px; flex-shrink:0; }

/* Empty */
.empty-col { min-height:300px; }
.empty-state { text-align:center; padding:60px 20px; }
.empty-icon { font-size:48px; display:block; margin-bottom:12px; }
.empty-state p { color:var(--text-muted); font-size:14px; margin:4px 0; }
.threshold-tips { margin-top:16px; display:flex; flex-direction:column; gap:6px; }
.tt { font-size:12px; background:#f9fafb; border-radius:6px; padding:6px 12px; color:var(--text-muted); }

.btn-copy-sm { font-size:11px; padding:4px 10px; border:1px solid var(--border); border-radius:6px; background:#fff; cursor:pointer; color:var(--text-muted); }
.copy-toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:#f0fdf4; border:1px solid var(--green-light); color:var(--green-dark); padding:10px 20px; border-radius:8px; font-size:13px; z-index:999; }
.error-msg { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:#fef2f2; border:1px solid #fca5a5; color:#dc2626; padding:10px 20px; border-radius:8px; font-size:13px; z-index:999; }
</style>
