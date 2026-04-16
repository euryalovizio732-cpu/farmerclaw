<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">📋 历史记录</h1>
      <p class="page-desc">最近 30 天生成记录，随时回查复用</p>
    </div>

    <div class="page-body">
      <!-- 汇总卡片 -->
      <div class="summary-row" v-if="summary">
        <div class="sum-card">
          <span class="sum-num">{{ summary.content_packs }}</span>
          <span class="sum-label">内容包</span>
        </div>
        <div class="sum-card">
          <span class="sum-num">{{ summary.listings }}</span>
          <span class="sum-label">Listing</span>
        </div>
        <div class="sum-card">
          <span class="sum-num">{{ summary.pain_points }}</span>
          <span class="sum-label">痛点分析</span>
        </div>
        <div class="sum-card total">
          <span class="sum-num">{{ total }}</span>
          <span class="sum-label">合计 / {{ days }}天</span>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="filter-bar card">
        <div class="filter-left">
          <button v-for="t in typeFilters" :key="t.value"
            :class="['filter-btn', activeType === t.value ? 'active' : '']"
            @click="activeType = t.value">
            {{ t.label }}
          </button>
        </div>
        <div class="filter-right">
          <select v-model="days" @change="load" class="form-select days-select">
            <option :value="7">最近7天</option>
            <option :value="14">最近14天</option>
            <option :value="30">最近30天</option>
          </select>
        </div>
      </div>

      <!-- 记录列表 -->
      <div class="records-area" v-if="!loading">
        <template v-if="filtered.length">
          <!-- 按日期分组 -->
          <template v-for="group in groupedRecords" :key="group.date">
            <div class="date-group">
              <div class="date-header">{{ formatDateHeader(group.date) }}</div>
              <div class="record-list">
                <div v-for="rec in group.records" :key="`${rec.type}-${rec.id}`"
                  :class="['record-card', `type-${rec.type}`]">

                  <!-- 类型图标 -->
                  <div class="rec-icon">{{ typeIcon(rec.type) }}</div>

                  <!-- 内容 -->
                  <div class="rec-body">
                    <div class="rec-top">
                      <span :class="['type-tag', `tag-${rec.type}`]">{{ typeLabel(rec.type) }}</span>
                      <span class="rec-product">{{ rec.product }}</span>
                      <span class="rec-category">{{ rec.category }}</span>
                    </div>

                    <!-- 内容包特有字段 -->
                    <div class="rec-detail" v-if="rec.type === 'content_pack'">
                      <span class="det">{{ rec.topics }} 个选题</span>
                      <span class="det">{{ rec.scripts }} 条口播稿</span>
                      <span class="det" v-if="rec.origin">{{ rec.origin }}</span>
                    </div>

                    <!-- Listing 特有字段 -->
                    <div class="rec-detail" v-if="rec.type === 'listing'">
                      <span class="det">{{ rec.platform }}</span>
                      <span :class="['compliance-dot', rec.compliance ? 'pass' : 'fail']">
                        {{ rec.compliance ? '✅ 合规' : '⚠️ 待修' }}
                      </span>
                      <span class="rec-title-preview" v-if="rec.title">「{{ rec.title }}」</span>
                    </div>

                    <!-- 痛点特有字段 -->
                    <div class="rec-detail" v-if="rec.type === 'pain_point'">
                      <span class="det">{{ rec.platform }}</span>
                    </div>

                    <div class="rec-time">{{ rec.created_at }}</div>
                  </div>

                  <!-- 操作 -->
                  <div class="rec-actions">
                    <button class="rec-btn detail-btn" @click="showDetail(rec)">查看详情</button>
                    <router-link :to="reLink(rec)" class="rec-btn">重新生成</router-link>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </template>

        <!-- 空状态 -->
        <div class="card empty-state" v-else>
          <span class="empty-icon">📭</span>
          <p>最近 {{ days }} 天暂无{{ activeType === 'all' ? '' : typeLabel(activeType) }}记录</p>
          <router-link to="/content-pack" class="btn btn-primary" style="margin-top:16px">去生成今日内容包</router-link>
        </div>
      </div>

      <!-- 加载中 -->
      <div class="loading-state" v-else>
        <div class="loading-spinner-lg"></div>
        <p>加载中...</p>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="modal-overlay" v-if="detailData" @click.self="detailData = null">
      <div :class="['modal', { wide: detailRec?.type === 'content_pack' }]">
        <div class="modal-header">
          <h3 class="modal-title">{{ typeLabel(detailRec?.type) }} 详情</h3>
          <button class="modal-close" @click="detailData = null">×</button>
        </div>
        <div class="modal-meta">
          <span class="rec-product">{{ detailData.product_name }}</span>
          <span class="rec-category">{{ detailData.category }}</span>
          <span class="rec-time">{{ detailData.created_at }}</span>
        </div>

        <!-- Listing 详情 -->
        <template v-if="detailRec?.type === 'listing'">
          <div class="detail-section">
            <div class="ds-label">标题</div>
            <div class="ds-content">{{ detailData.title }}</div>
          </div>
          <div class="detail-section" v-if="detailData.selling_points?.length">
            <div class="ds-label">卖点</div>
            <div class="ds-content">
              <div v-for="(sp, i) in detailData.selling_points" :key="i" class="sp-item">{{ typeof sp === 'string' ? sp : (sp.point || JSON.stringify(sp)) }}</div>
            </div>
          </div>
          <div class="detail-section" v-if="detailData.video_script">
            <div class="ds-label">口播稿</div>
            <div class="ds-content pre-wrap">{{ typeof detailData.video_script === 'object' ? (detailData.video_script.full_script || JSON.stringify(detailData.video_script, null, 2)) : detailData.video_script }}</div>
          </div>
          <div class="detail-section" v-if="detailData.live_script">
            <div class="ds-label">直播话术</div>
            <div class="ds-content pre-wrap">{{ typeof detailData.live_script === 'object' ? JSON.stringify(detailData.live_script, null, 2) : detailData.live_script }}</div>
          </div>
        </template>

        <!-- 痛点详情 -->
        <template v-if="detailRec?.type === 'pain_point'">
          <div class="detail-section" v-if="detailData.pain_points?.length">
            <div class="ds-label">TOP 痛点</div>
            <div class="ds-content">
              <div v-for="(pp, i) in detailData.pain_points" :key="i" class="pp-row">
                <strong>{{ i+1 }}. {{ pp.pain_point || pp.category || '' }}</strong>
                <span v-if="pp.opportunity"> — 💡 {{ pp.opportunity }}</span>
              </div>
            </div>
          </div>
          <div class="detail-section" v-if="detailData.pricing_suggestion">
            <div class="ds-label">定价建议</div>
            <div class="ds-content pre-wrap">{{ detailData.pricing_suggestion }}</div>
          </div>
        </template>

        <!-- 内容包详情 -->
        <template v-if="detailRec?.type === 'content_pack'">
          <div class="detail-section" v-if="detailData.history_note">
            <div class="notice-box">{{ detailData.history_note }}</div>
          </div>
          <div class="detail-section" v-if="detailData.request_payload">
            <div class="ds-label">原始输入</div>
            <div class="chip-row">
              <span class="det-chip" v-if="detailData.request_payload.product_name">产品：{{ detailData.request_payload.product_name }}</span>
              <span class="det-chip" v-if="detailData.request_payload.category">品类：{{ detailData.request_payload.category }}</span>
              <span class="det-chip" v-if="detailData.request_payload.origin">产地：{{ detailData.request_payload.origin }}</span>
              <span class="det-chip" v-if="detailData.request_payload.price">价格：{{ detailData.request_payload.price }}</span>
              <span class="det-chip" v-if="detailData.request_payload.core_features">卖点：{{ detailData.request_payload.core_features }}</span>
            </div>
          </div>
          <div class="detail-section" v-if="detailData.today?.tip">
            <div class="ds-label">今日建议</div>
            <div class="tip-box">
              <div class="tip-main">💡 {{ detailData.today.tip }}</div>
              <div class="tip-sub" v-if="detailData.today.season || detailData.today.solar_term">
                {{ [detailData.today.season, detailData.today.solar_term].filter(Boolean).join(' · ') }}
              </div>
            </div>
          </div>
          <div class="detail-section">
            <div class="ds-label">生成概要</div>
            <div class="ds-content">
              <span class="det">{{ detailData.topics_count }} 个选题</span>
              <span class="det">· {{ detailData.scripts_count }} 条口播稿</span>
            </div>
          </div>
          <div class="detail-section" v-if="detailData.stages_completed?.length">
            <div class="ds-label">完成阶段</div>
            <div class="ds-content">
              <span v-for="s in detailData.stages_completed" :key="s" class="stage-tag">✅ {{ s }}</span>
            </div>
          </div>
          <div class="detail-section" v-if="detailData.topics?.length">
            <div class="ds-label">选题</div>
            <div class="detail-grid two-col">
              <div v-for="topic in detailData.topics" :key="topic.topic_id || topic.title" class="detail-card">
                <div class="detail-card-title">{{ topic.title }}</div>
                <div class="detail-card-meta">
                  <span class="type-tag tag-content_pack">{{ topic.type || '选题' }}</span>
                  <span class="det" v-if="topic.estimated_completion_rate">{{ topic.estimated_completion_rate }}</span>
                </div>
                <div class="detail-lines">
                  <div v-if="topic.first_frame"><strong>封面：</strong>{{ topic.first_frame }}</div>
                  <div v-if="topic.shooting_angle"><strong>拍摄：</strong>{{ topic.shooting_angle }}</div>
                  <div v-if="topic.core_conflict"><strong>爆点：</strong>{{ topic.core_conflict }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="detail-section" v-if="detailData.scripts?.length">
            <div class="ds-label">口播稿</div>
            <div class="detail-stack">
              <div v-for="script in detailData.scripts" :key="script.topic_id || script.topic_title" class="detail-card">
                <div class="detail-card-title">{{ script.topic_title || `口播 ${script.topic_id || ''}` }}</div>
                <div class="detail-card-meta">
                  <span class="type-tag tag-content_pack">{{ script.topic_type || '口播' }}</span>
                  <span class="det" v-if="script.formula_type">{{ script.formula_type }}型</span>
                </div>
                <div class="detail-lines compact">
                  <div v-if="script.hook_0_3s"><strong>0-3s：</strong>{{ script.hook_0_3s }}</div>
                  <div v-if="script.product_3_15s"><strong>3-15s：</strong>{{ script.product_3_15s }}</div>
                  <div v-if="script.trust_15_25s"><strong>15-25s：</strong>{{ script.trust_15_25s }}</div>
                  <div v-if="script.cta_25_30s"><strong>25-30s：</strong>{{ script.cta_25_30s }}</div>
                </div>
                <div class="ds-content pre-wrap" v-if="script.full_script">{{ script.full_script }}</div>
              </div>
            </div>
          </div>
          <div class="detail-section" v-if="detailData.live_modules && Object.keys(detailData.live_modules).length">
            <div class="ds-label">直播话术</div>
            <div class="detail-stack">
              <div v-for="(modules, mtype) in detailData.live_modules" :key="mtype" class="detail-card">
                <div class="detail-card-title">{{ moduleLabel(mtype) }}</div>
                <div class="detail-lines compact">
                  <div v-for="m in modules" :key="m.id || m.name">
                    <strong>{{ m.name }}：</strong>{{ m.script }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="detail-section" v-if="detailData.hashtags?.length">
            <div class="ds-label">话题标签</div>
            <div class="chip-row">
              <span v-for="tag in detailData.hashtags" :key="tag" class="tag-chip">{{ tag }}</span>
            </div>
          </div>
        </template>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="copyDetail">复制全部内容</button>
          <router-link :to="reLink(detailRec)" class="btn btn-primary" @click="detailData = null">重新生成</router-link>
        </div>
      </div>
    </div>

    <div class="copy-toast" v-if="copyToast">✅ 已复制</div>
    <div class="detail-loading" v-if="detailLoading">加载中...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { dashboardApi } from '../api/index.js'


const days = ref(30)
const loading = ref(false)
const records = ref([])
const summary = ref(null)
const total = ref(0)
const activeType = ref('all')
const detailData = ref(null)
const detailRec = ref(null)
const detailLoading = ref(false)
const copyToast = ref(false)

const typeFilters = [
  { value: 'all', label: '全部' },
  { value: 'content_pack', label: '📦 内容包' },
  { value: 'listing', label: '✍️ Listing' },
  { value: 'pain_point', label: '🔍 痛点分析' },
]

const filtered = computed(() =>
  activeType.value === 'all' ? records.value : records.value.filter(r => r.type === activeType.value)
)

const groupedRecords = computed(() => {
  const groups = {}
  for (const rec of filtered.value) {
    const d = rec.date_only || rec.created_at.split(' ')[0]
    if (!groups[d]) groups[d] = []
    groups[d].push(rec)
  }
  return Object.entries(groups)
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([date, recs]) => ({ date, records: recs }))
})

const load = async () => {
  loading.value = true
  try {
    const res = await dashboardApi.getHistory(days.value)
    if (res.code === 0) {
      records.value = res.data.records
      summary.value = res.data.summary
      total.value = res.data.total
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const typeIcon = (t) => ({ content_pack: '📦', listing: '✍️', pain_point: '🔍' }[t] || '📄')
const typeLabel = (t) => ({ content_pack: '内容包', listing: 'Listing', pain_point: '痛点分析' }[t] || t)
const moduleLabel = (t) => ({ opening: '开场话术', product_intro: '产品介绍', interaction: '互动模块', urgency: '紧迫感模块', checkout: '催单成交' }[t] || t)
const reLink = (rec) => ({
  content_pack: '/content-pack',
  listing: '/listing',
  pain_point: '/pain-point',
}[rec.type] || '/')

const formatDateHeader = (dateStr) => {
  const today = new Date().toISOString().split('T')[0]
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
  if (dateStr === today) return `今天 · ${dateStr}`
  if (dateStr === yesterday) return `昨天 · ${dateStr}`
  return dateStr
}

const showDetail = async (rec) => {
  detailRec.value = rec
  detailLoading.value = true
  detailData.value = null
  try {
    const res = await dashboardApi.getHistoryDetail(rec.type, rec.id)
    if (res.code === 0) detailData.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    detailLoading.value = false
  }
}

const copyDetail = async () => {
  if (!detailData.value) return
  const text = JSON.stringify(detailData.value, null, 2)
  await navigator.clipboard.writeText(text).catch(() => {})
  copyToast.value = true
  setTimeout(() => copyToast.value = false, 2000)
}

onMounted(load)
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; display: flex; flex-direction: column; gap: 14px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }

/* Summary */
.summary-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.sum-card {
  background: #fff; border: 1px solid var(--border); border-radius: 10px;
  padding: 16px; text-align: center; display: flex; flex-direction: column; gap: 4px;
}
.sum-card.total { border-color: var(--green-light); background: var(--green-bg); }
.sum-num { font-size: 28px; font-weight: 800; color: var(--text); }
.sum-label { font-size: 12px; color: var(--text-muted); }

/* Filter */
.filter-bar { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; }
.filter-left { display: flex; gap: 6px; }
.filter-btn { padding: 5px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; background: #fff; color: var(--text-muted); }
.filter-btn.active { background: var(--green-primary); color: #fff; border-color: var(--green-primary); }
.days-select { font-size: 12px; padding: 5px 8px; border: 1px solid var(--border); border-radius: 6px; }

/* Date group */
.date-group { margin-bottom: 8px; }
.date-header { font-size: 12px; font-weight: 700; color: var(--text-muted); padding: 4px 0 8px; }
.record-list { display: flex; flex-direction: column; gap: 8px; }

/* Record card */
.record-card {
  background: #fff; border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; display: flex; align-items: flex-start; gap: 12px;
  transition: box-shadow .15s;
}
.record-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.record-card.type-content_pack { border-left: 3px solid var(--green-primary); }
.record-card.type-listing { border-left: 3px solid var(--orange-primary); }
.record-card.type-pain_point { border-left: 3px solid #8b5cf6; }

.rec-icon { font-size: 22px; margin-top: 2px; flex-shrink: 0; }
.rec-body { flex: 1; }
.rec-top { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; flex-wrap: wrap; }
.type-tag { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px; flex-shrink: 0; }
.tag-content_pack { background: var(--green-bg); color: var(--green-dark); }
.tag-listing { background: var(--orange-light); color: #c2410c; }
.tag-pain_point { background: #ede9fe; color: #6d28d9; }
.rec-product { font-size: 14px; font-weight: 700; }
.rec-category { font-size: 12px; color: var(--text-muted); background: #f3f4f6; padding: 1px 6px; border-radius: 4px; }

.rec-detail { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.det { font-size: 12px; color: var(--text-muted); }
.compliance-dot { font-size: 12px; font-weight: 600; }
.compliance-dot.pass { color: var(--green-dark); }
.compliance-dot.fail { color: #c2410c; }
.rec-title-preview { font-size: 12px; color: var(--text-muted); font-style: italic; }
.rec-time { font-size: 11px; color: #9ca3af; margin-top: 4px; }

.rec-actions { flex-shrink: 0; }
.rec-btn { font-size: 11px; padding: 5px 10px; border: 1px solid var(--border); border-radius: 6px; background: #fff; cursor: pointer; color: var(--text-muted); text-decoration: none; white-space: nowrap; }
.rec-btn:hover { background: var(--green-bg); color: var(--green-dark); border-color: var(--green-light); }

/* Loading */
.loading-state { text-align: center; padding: 60px; }
.loading-spinner-lg { width: 36px; height: 36px; border: 3px solid #e5e7eb; border-top-color: var(--green-primary); border-radius: 50%; animation: spin .7s linear infinite; display: inline-block; margin-bottom: 12px; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state { text-align: center; padding: 60px 20px; }
.empty-icon { font-size: 48px; display: block; margin-bottom: 12px; }
.empty-state p { color: var(--text-muted); font-size: 14px; }

.rec-actions { flex-shrink: 0; display: flex; gap: 6px; }
.detail-btn { background: var(--green-bg); color: var(--green-dark); border-color: var(--green-light); }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.45); z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 14px; padding: 24px; width: 640px; max-width: 92vw; max-height: 85vh; overflow-y: auto; }
.modal.wide { width: 980px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.modal-title { font-size: 16px; font-weight: 700; }
.modal-close { font-size: 22px; background: none; border: none; cursor: pointer; color: var(--text-muted); line-height: 1; }
.modal-meta { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }

.detail-section { margin-bottom: 14px; }
.ds-label { font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }
.ds-content { font-size: 13px; line-height: 1.7; color: var(--text); }
.ds-content.pre-wrap { white-space: pre-wrap; background: #f9fafb; border-radius: 8px; padding: 12px; max-height: 300px; overflow-y: auto; }
.notice-box { font-size: 13px; color: #92400e; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 10px 12px; }
.tip-box { background: var(--green-bg); border: 1px solid var(--green-light); border-radius: 8px; padding: 12px; }
.tip-main { font-size: 13px; font-weight: 600; color: var(--text); }
.tip-sub { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; }
.det-chip { font-size: 12px; background: #f9fafb; color: var(--text); border: 1px solid var(--border); border-radius: 999px; padding: 5px 10px; }
.tag-chip { font-size: 12px; background: var(--green-bg); color: var(--green-dark); border: 1px solid var(--green-light); border-radius: 999px; padding: 5px 10px; }
.detail-grid { display: grid; gap: 10px; }
.detail-grid.two-col { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.detail-stack { display: flex; flex-direction: column; gap: 10px; }
.detail-card { background: #f9fafb; border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
.detail-card-title { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
.detail-card-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
.detail-lines { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--text); }
.detail-lines.compact { font-size: 12px; }
.sp-item { padding: 3px 0; border-bottom: 1px dashed var(--border); }
.sp-item:last-child { border-bottom: none; }
.pp-row { padding: 4px 0; }
.stage-tag { display: inline-block; font-size: 12px; margin-right: 8px; }

.modal-footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border); }

@media (max-width: 900px) {
  .detail-grid.two-col { grid-template-columns: 1fr; }
}

.copy-toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #f0fdf4; border: 1px solid var(--green-light); color: var(--green-dark); padding: 10px 20px; border-radius: 8px; font-size: 13px; z-index: 999; }
.detail-loading { position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%); background: #fff; padding: 20px 32px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,.15); font-size: 14px; z-index: 101; }
</style>
