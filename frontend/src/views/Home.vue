<template>
  <div class="home-page">
    <!-- Hero -->
    <div class="hero">
      <div class="hero-content">
        <div class="hero-badge">🚀 三农电商 AI Agent · MVP v1.0</div>
        <h1 class="hero-title">三农电商，AI全自动运营</h1>
        <p class="hero-desc">
          适配抖音小店 · 拼多多 · 惠农网<br>
          从痛点挖掘到Listing生成，3分钟完成全套运营内容
        </p>
        <div class="hero-actions">
          <router-link to="/pain-point" class="btn btn-primary">
            🔍 开始痛点挖掘
          </router-link>
          <router-link to="/listing" class="btn btn-secondary">
            ✍️ 直接生成Listing
          </router-link>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat-item" v-for="s in stats" :key="s.label">
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- 功能模块 -->
    <div class="features-section">
      <h2 class="section-title">核心功能模块</h2>
      <div class="features-grid">
        <div
          v-for="f in features"
          :key="f.title"
          class="feature-card"
          @click="$router.push(f.route)"
        >
          <div class="feature-icon">{{ f.icon }}</div>
          <div class="feature-body">
            <div class="feature-title-row">
              <h3 class="feature-title">{{ f.title }}</h3>
              <span class="hot-badge" v-if="f.hot">HOT</span>
            </div>
            <p class="feature-desc">{{ f.desc }}</p>
            <div class="feature-tags">
              <span class="badge badge-green" v-for="t in f.tags" :key="t">{{ t }}</span>
            </div>
          </div>
          <div class="feature-arrow">→</div>
        </div>
      </div>
    </div>

    <!-- 工作流程 -->
    <div class="workflow-section">
      <h2 class="section-title">3步完成全套内容</h2>
      <div class="workflow-steps">
        <div class="step-item" v-for="(step, idx) in steps" :key="idx">
          <div class="step-number">{{ idx + 1 }}</div>
          <div class="step-icon">{{ step.icon }}</div>
          <h4 class="step-title">{{ step.title }}</h4>
          <p class="step-desc">{{ step.desc }}</p>
          <div class="step-arrow" v-if="idx < steps.length - 1">→</div>
        </div>
      </div>
    </div>

    <!-- 适配平台 -->
    <div class="platforms-section">
      <h2 class="section-title">适配平台</h2>
      <div class="platforms-grid">
        <div class="platform-card" v-for="p in platforms" :key="p.name">
          <span class="platform-icon">{{ p.icon }}</span>
          <div>
            <div class="platform-name">{{ p.name }}</div>
            <div class="platform-note">{{ p.note }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 知识库展示 -->
    <div class="kb-section">
      <h2 class="section-title">三农专属知识库</h2>
      <div class="kb-grid">
        <div class="kb-card" v-for="kb in knowledgeBases" :key="kb.title">
          <div class="kb-icon">{{ kb.icon }}</div>
          <div class="kb-title">{{ kb.title }}</div>
          <div class="kb-count">{{ kb.count }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const stats = [
  { value: '3分钟', label: '出全套内容' },
  { value: '14大', label: '品类词库' },
  { value: '100%', label: '合规校验' },
  { value: '997条', label: '真实样本库' },
]

const features = [
  {
    icon: '�',
    title: '爆款选题 + 口播稿',
    desc: '输入品类+产地+价格，3秒出3条爆款选题标题和可直接上镜念的口播稿，带节气时令策略',
    tags: ['选题标题', '口播脚本', '节气时令', '直接可用'],
    route: '/content-pack',
    hot: true,
  },
  {
    icon: '🔴',
    title: '直播话术积木',
    desc: '开场钩子 / 产品介绍 / 互动引导 / 促单逼单，5大模块随用随取，直播间不卡壳',
    tags: ['开场话术', '促单模块', '互动引导', '模块化'],
    route: '/listing',
  },
  {
    icon: '💬',
    title: '差评 / 售后话术',
    desc: '自动识别评论类型（质量投诉/催单/砍价/好评），生成场景化回复，引导晒图复购',
    tags: ['差评处理', '好评引导', '售后话术', '场景识别'],
    route: '/reply',
  },
  {
    icon: '�',
    title: '痛点挖掘 + 卖点提炼',
    desc: '分析品类TOP10用户痛点，提炼差异化卖点，输出竞品对标+定价建议+关键词机会',
    tags: ['痛点分析', '卖点提炼', '定价建议', '关键词'],
    route: '/pain-point',
  },
]

const steps = [
  {
    icon: '🔍',
    title: '痛点挖掘',
    desc: '输入品类+产品名，AI分析市场痛点',
  },
  {
    icon: '✍️',
    title: 'Listing生成',
    desc: '填入产品信息，一键生成全套内容',
  },
  {
    icon: '📋',
    title: '导出上架',
    desc: '复制内容，直接粘贴到对应平台',
  },
]

const platforms = [
  { icon: '📱', name: '抖音小店', note: '标题≤30字，视频口播' },
  { icon: '🛒', name: '拼多多', note: '标题≤60字，价格突出' },
  { icon: '🌾', name: '惠农网', note: '标题≤50字，专业化' },
  { icon: '🏪', name: '淘宝', note: '标题≤60字，SEO优化' },
  { icon: '📦', name: '京东', note: '标题≤60字，品质背书' },
  { icon: '🤝', name: '1688农业带', note: '批发话术，B2B风格' },
]

const knowledgeBases = [
  { icon: '🍊', title: '脐橙/苹果/草莓', count: '253条品类样本' },
  { icon: '🫐', title: '蓝莓/樱桃/猕猴桃', count: '213条品类样本' },
  { icon: '�', title: '芒果/桃子/葡萄/石榴', count: '171条品类样本' },
  { icon: '🥬', title: '蔬菜/粮油/通用', count: '274条品类样本' },
  { icon: '🎯', title: '直播话术模块', count: '30套积木式话术' },
  { icon: '🛡️', title: '合规词库', count: '60+ 禁用词 · 自动拦截' },
]
</script>

<style scoped>
.home-page { padding: 0; }

/* Hero */
.hero {
  background: linear-gradient(135deg, #14532d 0%, #166534 50%, #15803d 100%);
  padding: 48px 32px 40px;
  color: #fff;
}
.hero-content { max-width: 700px; }
.hero-badge {
  display: inline-block; background: rgba(255,255,255,.15); color: rgba(255,255,255,.9);
  font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 99px; margin-bottom: 16px;
}
.hero-title { font-size: 32px; font-weight: 800; line-height: 1.2; margin-bottom: 12px; }
.hero-desc { font-size: 15px; color: rgba(255,255,255,.8); line-height: 1.8; margin-bottom: 24px; }
.hero-actions { display: flex; gap: 12px; flex-wrap: wrap; }
.hero-actions .btn-secondary {
  background: rgba(255,255,255,.15); color: #fff; border-color: rgba(255,255,255,.3);
}
.hero-actions .btn-secondary:hover { background: rgba(255,255,255,.25); }

.hero-stats {
  display: flex; gap: 32px; margin-top: 32px; padding-top: 24px;
  border-top: 1px solid rgba(255,255,255,.15);
}
.stat-value { font-size: 24px; font-weight: 800; color: #4ade80; }
.stat-label { font-size: 12px; color: rgba(255,255,255,.65); margin-top: 2px; }

/* Sections */
.features-section, .workflow-section, .platforms-section, .kb-section {
  padding: 32px 32px;
}
.section-title {
  font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 20px;
}

/* Features */
.features-grid { display: flex; flex-direction: column; gap: 12px; }
.feature-card {
  display: flex; align-items: flex-start; gap: 16px;
  background: #fff; border-radius: 12px; padding: 20px;
  border: 1.5px solid var(--border); cursor: pointer;
  transition: all .15s ease;
}
.feature-card:hover { border-color: var(--green-primary); box-shadow: 0 4px 12px rgba(34,197,94,.12); transform: translateY(-1px); }
.feature-icon { font-size: 28px; flex-shrink: 0; }
.feature-body { flex: 1; }
.feature-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.feature-title { font-size: 15px; font-weight: 700; margin-bottom: 0; }
.hot-badge {
  font-size: 9px; font-weight: 800; background: #ef4444; color: #fff;
  border-radius: 4px; padding: 2px 6px; letter-spacing: .04em; flex-shrink: 0;
}
.feature-desc { font-size: 13px; color: var(--text-muted); margin-bottom: 10px; line-height: 1.6; }
.feature-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.feature-arrow { font-size: 18px; color: var(--text-muted); align-self: center; }

/* Workflow */
.workflow-steps {
  display: flex; gap: 0; align-items: flex-start;
  background: #fff; border-radius: 12px; border: 1px solid var(--border); overflow: hidden;
}
.step-item {
  flex: 1; padding: 24px 20px; text-align: center; position: relative;
  border-right: 1px solid var(--border);
}
.step-item:last-child { border-right: none; }
.step-number {
  width: 28px; height: 28px; background: var(--green-primary); color: #fff;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; margin: 0 auto 8px;
}
.step-icon { font-size: 28px; margin-bottom: 8px; }
.step-title { font-size: 14px; font-weight: 700; margin-bottom: 4px; }
.step-desc { font-size: 12px; color: var(--text-muted); }
.step-arrow {
  position: absolute; right: -12px; top: 50%; transform: translateY(-50%);
  font-size: 20px; color: var(--green-primary); z-index: 1;
}

/* Platforms */
.platforms-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.platform-card {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px;
}
.platform-icon { font-size: 22px; }
.platform-name { font-size: 14px; font-weight: 600; }
.platform-note { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

/* KB */
.kb-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.kb-card {
  background: #fff; border: 1px solid var(--border); border-radius: 10px;
  padding: 16px; text-align: center;
}
.kb-icon { font-size: 24px; margin-bottom: 6px; }
.kb-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.kb-count { font-size: 11px; color: var(--text-muted); }
</style>
