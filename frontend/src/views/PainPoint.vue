<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">🔍 爆品痛点挖掘 Agent</h1>
      <p class="page-desc">输入品类和产品名称，AI自动分析市场痛点，找到爆品差异化机会</p>
    </div>

    <div class="page-body">
      <!-- 输入表单 -->
      <div class="card form-card">
        <h3 class="card-title">分析参数设置</h3>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">品类 <span class="required">*</span></label>
            <select v-model="form.category" class="form-select">
              <option value="">请选择品类</option>
              <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">产品名称 <span class="required">*</span></label>
            <input
              v-model="form.product_name"
              class="form-input"
              placeholder="例如：赣南脐橙、云南松茸、东北大米"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">目标平台</label>
            <select v-model="form.platform" class="form-select">
              <option value="douyin">抖音小店</option>
              <option value="pinduoduo">拼多多</option>
              <option value="huinong">惠农网</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">月销量级别</label>
            <select v-model="form.sales_level" class="form-select">
              <option value="初期（月销0-500单）">初期（0-500单）</option>
              <option value="中等（月销1000-5000单）">中等（1000-5000单）</option>
              <option value="成熟（月销5000-50000单）">成熟（5000-50000单）</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">竞品描述（可选）</label>
          <textarea
            v-model="form.competitor_info"
            class="form-textarea"
            placeholder="描述主要竞品的特点、价格区间、评价情况，帮助AI更精准分析..."
            rows="3"
          ></textarea>
        </div>

        <div class="form-actions">
          <button
            class="btn btn-primary"
            @click="analyze"
            :disabled="loading || !form.category || !form.product_name"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-if="loading">AI分析中（约15-30秒）...</span>
            <span v-else>🚀 开始AI痛点分析</span>
          </button>
          <button class="btn btn-secondary" @click="resetForm">重置</button>
        </div>
      </div>

      <!-- 结果展示 -->
      <template v-if="result">
        <!-- 产品摘要 -->
        <div class="card">
          <div class="result-header">
            <h3 class="card-title">📋 市场概述</h3>
            <span class="badge badge-green">分析完成</span>
          </div>
          <p class="product-summary">{{ result.product_summary }}</p>
        </div>

        <!-- TOP痛点 -->
        <div class="card">
          <h3 class="card-title">🎯 TOP{{ result.top_pain_points.length }} 用户痛点</h3>
          <div class="pain-points-list">
            <div
              v-for="(pp, idx) in result.top_pain_points"
              :key="idx"
              class="pain-point-item"
            >
              <div class="pp-header">
                <div class="pp-rank">{{ pp.rank || idx + 1 }}</div>
                <div class="pp-meta">
                  <span class="pp-category">{{ pp.category }}</span>
                  <span :class="['badge', freqBadge(pp.frequency)]">{{ pp.frequency }}频次</span>
                </div>
              </div>
              <div class="pp-content">
                <div class="pp-pain"><strong>痛点：</strong>{{ pp.pain_point }}</div>
                <div class="pp-root" v-if="pp.root_cause"><strong>根因：</strong>{{ pp.root_cause }}</div>
                <div class="pp-opportunity highlight-box" v-if="pp.opportunity">
                  <span>💡 机会：</span>{{ pp.opportunity }}
                </div>
                <div class="pp-reviews" v-if="pp.sample_reviews?.length">
                  <span class="reviews-label">典型评价：</span>
                  <div class="review-item" v-for="r in pp.sample_reviews" :key="r">「{{ r }}」</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 差异化机会 -->
        <div class="card" v-if="result.differentiation_opportunities?.length">
          <h3 class="card-title">🚀 差异化机会点</h3>
          <div class="opp-list">
            <div
              v-for="(opp, idx) in result.differentiation_opportunities"
              :key="idx"
              class="opp-item"
            >
              <div class="opp-title">{{ opp.opportunity }}</div>
              <div class="opp-impl" v-if="opp.implementation">📌 {{ opp.implementation }}</div>
              <div class="opp-impact" v-if="opp.expected_impact">📈 {{ opp.expected_impact }}</div>
            </div>
          </div>
        </div>

        <!-- 定价建议 + 关键词 + 快赢 -->
        <div class="bottom-grid">
          <div class="card">
            <h3 class="card-title">💰 定价建议</h3>
            <div v-if="result.pricing_suggestion" class="pricing-info">
              <div class="pricing-row">
                <span class="pricing-label">建议区间</span>
                <span class="pricing-value">{{ result.pricing_suggestion.suggested_price_range }}</span>
              </div>
              <div class="pricing-row" v-if="result.pricing_suggestion.pricing_strategy">
                <span class="pricing-label">定价策略</span>
                <span class="pricing-value">{{ result.pricing_suggestion.pricing_strategy }}</span>
              </div>
              <div class="pricing-row" v-if="result.pricing_suggestion.anchor_price">
                <span class="pricing-label">锚点设置</span>
                <span class="pricing-value">{{ result.pricing_suggestion.anchor_price }}</span>
              </div>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title">🔑 关键词机会</h3>
            <div class="keywords-list">
              <span
                v-for="kw in result.keyword_opportunities"
                :key="kw"
                class="kw-tag"
              >{{ kw }}</span>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title">⚡ 3天快赢动作</h3>
            <ul class="quick-wins-list">
              <li v-for="(qw, idx) in result.quick_wins" :key="idx">
                <span class="qw-num">{{ idx + 1 }}</span>{{ qw }}
              </li>
            </ul>
          </div>
        </div>

        <!-- 用Listing生成 -->
        <div class="card cta-card">
          <div class="cta-content">
            <span class="cta-icon">✍️</span>
            <div>
              <div class="cta-title">基于痛点分析，生成全套 Listing</div>
              <div class="cta-desc">将此分析结果直接用于 Listing 生成，内容更精准</div>
            </div>
            <router-link
              :to="{ path: '/listing', query: { category: form.category, product_name: form.product_name, pain_summary: topPainSummary } }"
              class="btn btn-orange"
            >
              去生成 Listing →
            </router-link>
          </div>
        </div>

        <!-- 反馈栏 -->
        <div class="card feedback-bar" v-if="!feedbackDone">
          <span class="fb-label">这份痛点分析报告：</span>
          <button class="fb-btn usable" @click="submitFeedback('usable')">✅ 准确有用</button>
          <button class="fb-btn edit" @click="submitFeedback('needs_edit')">✏️ 部分准确</button>
          <button class="fb-btn bad" @click="submitFeedback('unusable')">❌ 不准确</button>
        </div>
        <div class="fb-done" v-else>✅ 反馈已记录，感谢！</div>
      </template>

      <!-- 空状态 -->
      <div class="card empty-state" v-else-if="!loading">
        <span class="empty-icon">🌾</span>
        <p>输入品类和产品名称，点击"开始AI痛点分析"</p>
        <p style="font-size:12px;margin-top:8px;color:#9ca3af">分析时间约15-30秒，请耐心等待</p>
      </div>
    </div>

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
import { painPointApi, feedbackApi } from '../api/index.js'

const route = useRoute()

const categories = ref(['脐橙', '苹果', '草莓', '樱桃', '蓝莓', '猕猴桃', '芒果', '桃子', '葡萄', '西瓜', '沃柑', '石榴', '蔬菜', '粮油'])
const form = ref({
  category: route.query.category || '',
  product_name: route.query.product_name || '',
  platform: 'douyin',
  sales_level: '中等（月销1000-5000单）',
  competitor_info: '',
})
const loading = ref(false)
const result = ref(null)
const error = ref('')
const feedbackDone = ref(false)

const freqBadge = (freq) => {
  if (freq === '高') return 'badge-red'
  if (freq === '中') return 'badge-orange'
  return 'badge-gray'
}

const topPainSummary = computed(() => {
  if (!result.value?.top_pain_points?.length) return ''
  return result.value.top_pain_points.slice(0, 3).map(p => p.pain_point).join('；')
})

const analyze = async () => {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const res = await painPointApi.analyze(form.value)
    if (res.code === 0) {
      result.value = res.data
    } else {
      error.value = res.message || '分析失败'
    }
  } catch (e) {
    error.value = e.message || '网络请求失败'
  } finally {
    loading.value = false
  }
}

const submitFeedback = async (rating) => {
  feedbackDone.value = true
  try {
    await feedbackApi.submit({
      content_type: 'pain_point',
      content_id: 'report',
      product_name: form.value.product_name,
      category: form.value.category,
      rating,
      edited_text: rating === 'usable' ? JSON.stringify(result.value) : '',
      comment: '',
    })
  } catch {}
}

const resetForm = () => {
  form.value = { category: '', product_name: '', platform: 'douyin', sales_level: '中等（月销1000-5000单）', competitor_info: '' }
  result.value = null
  error.value = ''
  feedbackDone.value = false
}

onMounted(async () => {
  try {
    const res = await painPointApi.getCategories()
    if (res.data?.length) categories.value = res.data
  } catch {}
})
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; display: flex; flex-direction: column; gap: 16px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.card-title { font-size: 15px; font-weight: 700; margin-bottom: 16px; }
.form-card {}
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-actions { display: flex; gap: 10px; margin-top: 8px; }

.result-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.result-header .card-title { margin-bottom: 0; }
.product-summary { color: var(--text-muted); line-height: 1.8; }

/* Pain Points */
.pain-points-list { display: flex; flex-direction: column; gap: 12px; }
.pain-point-item { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.pp-header { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: var(--green-bg); }
.pp-rank {
  width: 28px; height: 28px; background: var(--green-primary); color: #fff;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.pp-meta { display: flex; align-items: center; gap: 8px; }
.pp-category { font-weight: 600; font-size: 13px; }
.pp-content { padding: 12px 16px; display: flex; flex-direction: column; gap: 8px; }
.pp-pain, .pp-root { font-size: 13px; line-height: 1.6; }
.highlight-box {
  background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px;
  padding: 8px 12px; font-size: 13px; line-height: 1.6;
}
.pp-reviews { font-size: 12px; color: var(--text-muted); }
.reviews-label { font-weight: 600; }
.review-item { margin-top: 2px; }

/* Opportunities */
.opp-list { display: flex; flex-direction: column; gap: 10px; }
.opp-item { background: var(--green-bg); border-radius: 8px; padding: 12px 16px; }
.opp-title { font-weight: 600; margin-bottom: 6px; }
.opp-impl, .opp-impact { font-size: 12px; color: var(--text-muted); margin-top: 3px; }

/* Bottom Grid */
.bottom-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.pricing-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed var(--border); font-size: 13px; }
.pricing-row:last-child { border-bottom: none; }
.pricing-label { color: var(--text-muted); }
.pricing-value { font-weight: 600; max-width: 60%; text-align: right; }

.keywords-list { display: flex; flex-wrap: wrap; gap: 8px; }
.kw-tag {
  background: var(--green-light); color: var(--green-dark); border-radius: 6px;
  padding: 4px 10px; font-size: 12px; font-weight: 500;
}

.quick-wins-list { list-style: none; display: flex; flex-direction: column; gap: 8px; }
.quick-wins-list li { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; line-height: 1.5; }
.qw-num {
  width: 20px; height: 20px; background: var(--orange-primary); color: #fff;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0; margin-top: 1px;
}

/* CTA */
.cta-card { background: linear-gradient(135deg, #fff7ed, #fff); border-color: var(--orange-light); }
.cta-content { display: flex; align-items: center; gap: 16px; }
.cta-icon { font-size: 32px; }
.cta-title { font-weight: 700; font-size: 15px; }
.cta-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* Feedback */
.feedback-bar { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.fb-label { font-size: 12px; color: var(--text-muted); margin-right: 4px; }
.fb-btn { font-size: 11px; padding: 4px 10px; border-radius: 6px; border: 1px solid; cursor: pointer; font-weight: 600; }
.fb-btn.usable { border-color: var(--green-light); color: var(--green-dark); background: var(--green-bg); }
.fb-btn.edit { border-color: #fde68a; color: #92400e; background: #fffbeb; }
.fb-btn.bad { border-color: #fca5a5; color: #dc2626; background: #fef2f2; }
.fb-done { font-size: 12px; color: var(--green-dark); padding: 10px 0; }

/* Error Toast */
.error-toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  background: #fef2f2; border: 1px solid #fca5a5; color: #dc2626;
  padding: 10px 16px; border-radius: 8px; font-size: 13px; z-index: 999;
  box-shadow: var(--shadow-md);
}
</style>
