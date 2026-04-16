<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">📊 数据看板</h1>
      <p class="page-desc">平台使用统计、合规数据、知识库状态</p>
    </div>

    <div class="page-body" v-if="stats">
      <!-- 核心指标 -->
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-icon">🔍</div>
          <div class="metric-value">{{ stats.total_analyses }}</div>
          <div class="metric-label">痛点分析次数</div>
        </div>
        <div class="metric-card">
          <div class="metric-icon">✍️</div>
          <div class="metric-value">{{ stats.total_listings }}</div>
          <div class="metric-label">Listing生成次数</div>
        </div>
        <div class="metric-card">
          <div class="metric-icon">📦</div>
          <div class="metric-value">{{ stats.total_packs }}</div>
          <div class="metric-label">内容包生成次数</div>
        </div>
        <div class="metric-card">
          <div class="metric-icon">👥</div>
          <div class="metric-value">{{ stats.total_users }}</div>
          <div class="metric-label">注册用户数</div>
        </div>
        <div class="metric-card green">
          <div class="metric-icon">✅</div>
          <div class="metric-value">{{ stats.compliance_pass_rate }}%</div>
          <div class="metric-label">合规通过率</div>
        </div>
      </div>

      <div class="charts-row">
        <!-- 品类分布 -->
        <div class="card chart-card">
          <h3 class="card-title">品类分布</h3>
          <div class="bar-chart">
            <div
              v-for="cat in stats.top_categories"
              :key="cat.name"
              class="bar-row"
            >
              <div class="bar-label">{{ cat.name }}</div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: barWidth(cat.count, stats.top_categories) + '%' }"
                ></div>
              </div>
              <div class="bar-count">{{ cat.count }}</div>
            </div>
          </div>
        </div>

        <!-- 平台分布 -->
        <div class="card chart-card">
          <h3 class="card-title">平台分布</h3>
          <div class="bar-chart">
            <div
              v-for="plat in stats.top_platforms"
              :key="plat.name"
              class="bar-row"
            >
              <div class="bar-label">{{ plat.name }}</div>
              <div class="bar-track">
                <div
                  class="bar-fill orange"
                  :style="{ width: barWidth(plat.count, stats.top_platforms) + '%' }"
                ></div>
              </div>
              <div class="bar-count">{{ plat.count }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 知识库状态 -->
      <div class="card" v-if="kbStats">
        <h3 class="card-title">🧠 三农知识库状态</h3>
        <div class="kb-metrics">
          <div class="kb-metric" v-for="(val, key) in kbStatDisplay" :key="key">
            <div class="kb-icon">{{ val.icon }}</div>
            <div class="kb-value">{{ val.value }}</div>
            <div class="kb-label">{{ val.label }}</div>
          </div>
        </div>
      </div>

      <!-- Few-shot 样本库状态 -->
      <div class="card" v-if="sampleLibStats">
        <h3 class="card-title">🎯 Few-shot 样本库状态</h3>
        <div class="sample-status-bar">
          <span :class="['sample-status-badge', sampleReadyClass]">{{ sampleReadyText }}</span>
          <span class="sample-hint">样本库就绪后，AI生成内容将自动绑定真实爆款风格</span>
        </div>
        <div class="sample-metrics">
          <div class="sample-metric">
            <div class="sample-val">{{ sampleLibStats.total_samples }}</div>
            <div class="sample-lbl">已录入样本总量</div>
            <div class="sample-target">目标：400条</div>
          </div>
          <div class="sample-metric">
            <div class="sample-val">{{ sampleLibStats.validated_samples }}</div>
            <div class="sample-lbl">商家验证「直接可用」</div>
            <div class="sample-target">目标：100条</div>
          </div>
          <div class="sample-metric">
            <div class="sample-val">{{ sampleLibStats.categories_with_samples }}</div>
            <div class="sample-lbl">已有样本品类数</div>
            <div class="sample-target">目标：8个品类 ✅</div>
          </div>
        </div>
        <div class="sample-guide" v-if="!sampleLibStats.is_ready">
          <p>📋 <strong>填充步骤：</strong>从抖音三农爆款视频采集口播文本 → 整理到 <code>sample_library.py</code> → 重启后端即生效</p>
        </div>
      </div>

      <!-- 反馈效果统计 -->
      <div class="card" v-if="fbStats">
        <h3 class="card-title">📊 内容质量反馈（商家评价）</h3>
        <div class="fb-metrics">
          <div class="fb-metric">
            <div class="fb-val big" :class="fbStats.usable_rate >= 70 ? 'val-good' : 'val-warn'">{{ fbStats.usable_rate }}%</div>
            <div class="fb-lbl">直接可用率</div>
            <div class="fb-target">目标：70%</div>
          </div>
          <div class="fb-metric">
            <div class="fb-val">{{ fbStats.total }}</div>
            <div class="fb-lbl">反馈总数</div>
          </div>
          <div class="fb-metric">
            <div class="fb-val val-good">{{ fbStats.usable }}</div>
            <div class="fb-lbl">直接可用</div>
          </div>
          <div class="fb-metric">
            <div class="fb-val val-edit">{{ fbStats.needs_edit }}</div>
            <div class="fb-lbl">改了能用</div>
          </div>
          <div class="fb-metric">
            <div class="fb-val val-bad">{{ fbStats.unusable }}</div>
            <div class="fb-lbl">不能用</div>
          </div>
        </div>
        <div class="fb-bar-wrap">
          <div class="fb-bar-track">
            <div class="fb-bar-fill" :style="{width: Math.min(fbStats.usable_rate, 100) + '%'}"></div>
            <div class="fb-bar-target" style="left:70%"></div>
          </div>
          <div class="fb-bar-labels">
            <span>0%</span>
            <span class="fb-target-label">目标 70%</span>
            <span>100%</span>
          </div>
        </div>
        <div class="fb-gap" v-if="fbStats.gap > 0">⚠️ 距离目标还差 <strong>{{ fbStats.gap }}%</strong>，需要继续优化 Prompt + 填充真实样本</div>
        <div class="fb-gap good" v-else-if="fbStats.total > 0">✅ 可用率已达标！继续保持</div>
      </div>

      <!-- 最近 Listing 记录 -->
      <div class="card">
        <h3 class="card-title">最近 Listing 生成</h3>
        <div class="records-table" v-if="stats.recent_listings?.length">
          <div class="table-header">
            <span>产品</span>
            <span>平台</span>
            <span>合规状态</span>
            <span>生成时间</span>
          </div>
          <div
            v-for="record in stats.recent_listings"
            :key="record.created_at + record.product"
            class="table-row"
          >
            <span class="record-product">{{ record.product }}</span>
            <span class="badge badge-gray">{{ record.platform }}</span>
            <span :class="['badge', record.compliance ? 'badge-green' : 'badge-red']">
              {{ record.compliance ? '✅ 通过' : '⚠️ 有问题' }}
            </span>
            <span class="record-date">{{ record.created_at }}</span>
          </div>
        </div>
        <div class="empty-table" v-else>暂无记录</div>
      </div>

      <!-- 最近内容包记录 -->
      <div class="card" v-if="stats.recent_packs?.length">
        <h3 class="card-title">最近内容包</h3>
        <div class="records-table">
          <div class="table-header">
            <span>产品</span>
            <span>品类</span>
            <span>话题数</span>
            <span>生成时间</span>
          </div>
          <div
            v-for="pack in stats.recent_packs"
            :key="pack.created_at + pack.product"
            class="table-row"
          >
            <span class="record-product">{{ pack.product }}</span>
            <span class="badge badge-gray">{{ pack.category }}</span>
            <span class="badge badge-green">{{ pack.topics }} 个话题</span>
            <span class="record-date">{{ pack.created_at }}</span>
          </div>
        </div>
      </div>

      <!-- 定价方案 -->
      <div class="card">
        <h3 class="card-title">💼 服务套餐（内测定价）</h3>
        <div class="pricing-grid">
          <div class="pricing-plan" v-for="plan in pricingPlans" :key="plan.name">
            <div :class="['plan-badge', plan.badge]">{{ plan.tag }}</div>
            <div class="plan-name">{{ plan.name }}</div>
            <div class="plan-price">{{ plan.price }}<span class="plan-unit">/月</span></div>
            <ul class="plan-features">
              <li v-for="f in plan.features" :key="f">✓ {{ f }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div class="page-body" v-else>
      <div class="card empty-state">
        <span class="empty-icon">📊</span>
        <p>数据加载中...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { dashboardApi, feedbackApi } from '../api/index.js'

const stats = ref(null)
const kbStats = ref(null)
const fbStats = ref(null)

const barWidth = (val, list) => {
  const max = Math.max(...list.map(i => i.count))
  return Math.round((val / max) * 100)
}

const kbStatDisplay = computed(() => {
  if (!kbStats.value) return {}
  return {
    categories: { icon: '🗂️', value: kbStats.value.categories, label: '品类数' },
    total_keywords: { icon: '🔑', value: kbStats.value.total_keywords + '+', label: '词库总量' },
    pain_point_categories: { icon: '🎯', value: kbStats.value.pain_point_categories, label: '痛点分类' },
    compliance_rules: { icon: '🚫', value: kbStats.value.compliance_rules, label: '合规规则' },
    listing_templates: { icon: '📝', value: kbStats.value.listing_templates, label: 'Listing模板' },
  }
})

const sampleLibStats = computed(() => kbStats.value?.sample_library || null)
const sampleReadyClass = computed(() => {
  if (!sampleLibStats.value) return 'status-empty'
  return sampleLibStats.value.is_ready ? 'status-ready' : 'status-pending'
})
const sampleReadyText = computed(() => {
  if (!sampleLibStats.value) return '加载中'
  return sampleLibStats.value.is_ready ? '✅ 已就绪（Few-shot已启用）' : '⏳ 待填充（当前纯指令模式）'
})

const pricingPlans = [
  {
    name: '基础版',
    tag: '内测',
    badge: 'badge-gray',
    price: '498',
    features: ['痛点挖掘Agent', 'Listing生成Agent', '合规检测', '抖音/拼多多适配', '每月500次调用'],
  },
  {
    name: '专业版',
    tag: '推荐',
    badge: 'badge-green',
    price: '1280',
    features: ['全部基础功能', '投放优化Agent（即将上线）', '评价维护Agent（即将上线）', '不限调用次数', '优先客服支持'],
  },
  {
    name: '企业版',
    tag: '1v1陪跑',
    badge: 'badge-orange',
    price: '3980',
    features: ['全部专业功能', '多店铺管理', '专属运营顾问', '1v1陪跑服务', '定制化功能开发'],
  },
]

onMounted(async () => {
  try {
    const [statsRes, kbRes, fbRes] = await Promise.all([
      dashboardApi.getStats(),
      dashboardApi.getKbStats(),
      feedbackApi.stats(),
    ])
    if (statsRes.code === 0) stats.value = statsRes.data
    if (kbRes.code === 0) kbStats.value = kbRes.data
    if (fbRes.code === 0) fbStats.value = fbRes.data
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; display: flex; flex-direction: column; gap: 16px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.card-title { font-size: 15px; font-weight: 700; margin-bottom: 16px; }

.metrics-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.metric-card {
  background: #fff; border-radius: 12px; padding: 20px 16px; text-align: center;
  border: 1px solid var(--border);
}
.metric-card.green { border-color: var(--green-light); background: var(--green-bg); }
.metric-icon { font-size: 24px; margin-bottom: 8px; }
.metric-value { font-size: 28px; font-weight: 800; color: var(--text); }
.metric-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.chart-card {}
.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: flex; align-items: center; gap: 10px; }
.bar-label { font-size: 13px; width: 80px; flex-shrink: 0; }
.bar-track { flex: 1; height: 10px; background: #f3f4f6; border-radius: 99px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--green-primary); border-radius: 99px; transition: width .5s ease; }
.bar-fill.orange { background: var(--orange-primary); }
.bar-count { font-size: 12px; color: var(--text-muted); width: 30px; text-align: right; }
.empty-table { font-size: 13px; color: var(--text-muted); padding: 20px 0; text-align: center; }

.kb-metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.kb-metric { text-align: center; padding: 12px 8px; background: var(--green-bg); border-radius: 8px; }
.kb-icon { font-size: 20px; margin-bottom: 4px; }
.kb-value { font-size: 18px; font-weight: 700; color: var(--green-dark); }
.kb-label { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.records-table { display: flex; flex-direction: column; gap: 0; }
.table-header {
  display: grid; grid-template-columns: 2fr 1fr 1fr 1fr;
  padding: 8px 12px; background: #f9fafb; border-radius: 6px;
  font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px;
}
.table-row {
  display: grid; grid-template-columns: 2fr 1fr 1fr 1fr;
  padding: 10px 12px; border-bottom: 1px solid var(--border); align-items: center; font-size: 13px;
}
.table-row:last-child { border-bottom: none; }
.record-product { font-weight: 600; }
.record-date { color: var(--text-muted); }

.sample-status-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.sample-status-badge { padding: 4px 12px; border-radius: 99px; font-size: 12px; font-weight: 700; }
.status-ready { background: var(--green-bg); color: var(--green-dark); }
.status-pending { background: #fff7ed; color: #c2410c; }
.status-empty { background: #f3f4f6; color: var(--text-muted); }
.sample-hint { font-size: 12px; color: var(--text-muted); }
.sample-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px; }
.sample-metric { text-align: center; padding: 12px; background: #f9fafb; border-radius: 8px; }
.sample-val { font-size: 24px; font-weight: 800; color: var(--text); }
.sample-lbl { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.sample-target { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.sample-guide { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 10px 14px; }
.sample-guide p { font-size: 12px; color: #92400e; margin: 0; }
.sample-guide code { background: #fef3c7; padding: 1px 4px; border-radius: 3px; font-size: 11px; }

/* Feedback Stats */
.fb-metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 16px; }
.fb-metric { text-align: center; padding: 12px 8px; background: #f9fafb; border-radius: 8px; }
.fb-val { font-size: 18px; font-weight: 800; color: var(--text); }
.fb-val.big { font-size: 28px; }
.fb-val.val-good { color: var(--green-dark); }
.fb-val.val-warn { color: #c2410c; }
.fb-val.val-edit { color: #92400e; }
.fb-val.val-bad { color: #dc2626; }
.fb-lbl { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.fb-target { font-size: 10px; color: #9ca3af; }
.fb-bar-wrap { margin-bottom: 12px; }
.fb-bar-track { height: 12px; background: #f3f4f6; border-radius: 6px; position: relative; overflow: visible; }
.fb-bar-fill { height: 100%; background: linear-gradient(90deg, #f59e0b, var(--green-primary)); border-radius: 6px; transition: width .6s; }
.fb-bar-target { position: absolute; top: -4px; bottom: -4px; width: 2px; background: #dc2626; border-radius: 1px; }
.fb-bar-labels { display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted); margin-top: 4px; }
.fb-target-label { color: #dc2626; font-weight: 600; }
.fb-gap { font-size: 12px; color: #92400e; background: #fffbeb; border: 1px solid #fde68a; padding: 8px 12px; border-radius: 8px; }
.fb-gap.good { color: var(--green-dark); background: var(--green-bg); border-color: var(--green-light); }

.pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.pricing-plan {
  border: 1.5px solid var(--border); border-radius: 12px; padding: 20px; position: relative;
}
.plan-badge {
  display: inline-block; padding: 2px 10px; border-radius: 99px;
  font-size: 11px; font-weight: 700; margin-bottom: 10px;
}
.plan-name { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
.plan-price { font-size: 28px; font-weight: 800; color: var(--green-dark); margin-bottom: 14px; }
.plan-unit { font-size: 13px; font-weight: 400; color: var(--text-muted); }
.plan-features { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.plan-features li { font-size: 12px; color: var(--text-muted); }
</style>
