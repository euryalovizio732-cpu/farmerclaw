<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">💰 内测定价 & 商家邀约</h1>
      <p class="page-desc">Day14 内测物料 — 定价方案 / 邀约话术 / 快速上手SOP</p>
    </div>

    <div class="page-body">
      <!-- 定价卡片 -->
      <div class="section-title">📦 三档定价方案</div>
      <div class="pricing-grid">
        <div v-for="plan in plans" :key="plan.tier" :class="['pricing-card', plan.highlight ? 'featured' : '']">
          <div class="plan-badge" v-if="plan.badge">{{ plan.badge }}</div>
          <div class="plan-name">{{ plan.name }}</div>
          <div class="plan-price">
            <span class="price-num">{{ plan.price }}</span>
            <span class="price-unit">/月</span>
          </div>
          <div class="plan-annual" v-if="plan.annual">年付 {{ plan.annual }} · 省{{ plan.save }}</div>
          <div class="plan-target">适合：{{ plan.target }}</div>
          <ul class="plan-features">
            <li v-for="f in plan.features" :key="f">✅ {{ f }}</li>
          </ul>
          <div class="plan-cta">{{ plan.cta }}</div>
        </div>
      </div>

      <!-- 邀约话术 -->
      <div class="section-title">🎙️ 商家邀约话术（微信发送）</div>
      <div class="card">
        <div class="tab-row">
          <button v-for="t in speechTabs" :key="t.key" :class="['tab-sm', {active: speechTab===t.key}]" @click="speechTab=t.key">{{ t.label }}</button>
        </div>
        <div class="speech-box">
          <div class="speech-text">{{ speeches[speechTab] }}</div>
          <button class="btn btn-secondary copy-btn" @click="copy(speeches[speechTab])">复制话术</button>
        </div>
      </div>

      <!-- 3天上手SOP -->
      <div class="section-title">📋 3天快速上手SOP（发给商家）</div>
      <div class="card sop-card">
        <div class="sop-day" v-for="day in sop" :key="day.day">
          <div class="sop-day-header">
            <span class="sop-day-num">Day {{ day.day }}</span>
            <span class="sop-day-title">{{ day.title }}</span>
          </div>
          <div class="sop-steps">
            <div class="sop-step" v-for="(step, i) in day.steps" :key="i">
              <span class="sop-num">{{ i+1 }}</span>{{ step }}
            </div>
          </div>
          <div class="sop-goal">🎯 今日目标：{{ day.goal }}</div>
        </div>
        <button class="btn btn-secondary" @click="copy(sopText)" style="margin-top:12px">复制全部SOP</button>
      </div>

      <!-- 免责声明 -->
      <div class="section-title">📄 免费内测协议核心条款</div>
      <div class="card disclaimer-card">
        <div class="disclaimer-item" v-for="(item, i) in disclaimer" :key="i">
          <span class="dis-num">{{ i+1 }}</span>
          <div>
            <div class="dis-title">{{ item.title }}</div>
            <div class="dis-content">{{ item.content }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="copy-toast" v-if="copyToast">✅ 已复制</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const copyToast = ref(false)
const speechTab = ref('wechat_short')

const plans = [
  {
    tier: 'basic', name: '基础版', price: '498', annual: '4780元', save: '200元',
    target: '小商家，月销5-20万，1-2个品',
    features: ['今日内容包不限次', '痛点分析200次/月', 'Listing生成200次/月', '抖音合规自动检测', '标准客服支持'],
    cta: '内测期：免费使用', badge: '', highlight: false,
  },
  {
    tier: 'pro', name: '专业版', price: '1280', annual: '12000元', save: '1560元',
    target: '中商家，月销20-100万，多品运营',
    features: ['全部基础版功能', '使用次数不限', '投放优化Agent（即将上线）', '评价维护Agent（即将上线）', '优先客服 + 专属群'],
    cta: '内测期：5折 640元/月', badge: '🔥 推荐', highlight: true,
  },
  {
    tier: 'enterprise', name: '企业版', price: '3980', annual: '36000元', save: '9760元',
    target: '大商家/合作社，多店铺，有团队',
    features: ['全部专业版功能', '多店铺管理（5个以内）', '专属运营顾问1v1', '定制化知识库', '每月效果报告'],
    cta: '内测期：联系洽谈', badge: '', highlight: false,
  },
]

const speechTabs = [
  { key: 'wechat_short', label: '微信短消息' },
  { key: 'wechat_long', label: '朋友圈文案' },
  { key: 'group_msg', label: '群发话术' },
]

const speeches = {
  wechat_short: `老板好！我是做三农电商AI工具的，最近在找抖音农产品商家内测。

我们做了个AI工具，专门帮三农商家自动生成：
✅ 3条抖音选题（含封面建议）
✅ 3条口播稿（可直接念，不用自己想）
✅ 直播话术积木块（2小时直播用）

现在内测免费用，只要你用完给我们反馈就行。

您有兴趣试试吗？3分钟就能出一套内容，比自己写省2小时。`,

  wechat_long: `【内测招募】三农抖音商家，你还在自己想选题写口播？

我做了个AI工具，专门帮三农商家每天3分钟搞定内容：
🎬 3条爆款选题方向（结合当季时令）
🎙️ 3篇30秒口播稿（可直接念，口语化）
🔴 完整直播话术积木块

现在招募10家合作社/产地商家内测，完全免费，只求真实反馈。

你家是卖什么的？发我看看适不适合 👇`,

  group_msg: `@各位老板 我们团队最近做了个三农电商AI工具，现在在找抖音农产品商家内测。

核心功能：每天3分钟，自动出：
• 3条选题（告诉你今天拍什么、怎么拍）
• 3篇口播稿（30秒，可直接念）
• 直播话术（模块化，自由拼接）

内测期完全免费，只需要：①正常使用 ②用完给反馈

感兴趣私聊我 🙋`,
}

const sop = [
  {
    day: 1, title: '注册 + 生成第一个内容包',
    steps: [
      '打开 FarmerClaw，点「免费注册」，填邮箱和密码',
      '登录后点左侧「今日内容包」',
      '填写：产品名称（你家卖的）+ 品类 + 产地 + 价格',
      '点「一键生成今日内容包」，等30秒',
      '看一下生成的3条选题，选一条你觉得能拍的',
      '复制对应的口播稿，今天发布一条视频',
    ],
    goal: '成功生成第一个内容包，发布第一条AI口播视频',
  },
  {
    day: 2, title: '用直播话术积木块完成一场直播',
    steps: [
      '进入「今日内容包」，切换到「直播话术积木」标签',
      '找「开场话术」，选一条复制到备忘录',
      '找「产品介绍」，复制，改成你家产品的具体信息',
      '找「紧迫感话术」和「催单话术」各选一条',
      '今天直播时按：开场 → 产品介绍 → 紧迫感 → 催单 顺序用',
      '直播后记录：哪段话反应最好，哪段需要改',
    ],
    goal: '完成第一场用AI话术的直播，记录效果对比',
  },
  {
    day: 3, title: '对比数据 + 给我们反馈',
    steps: [
      '查看这2天发的AI口播视频vs之前视频的完播率',
      '查看昨天直播的转化数据（下单数/加购数）',
      '在微信发给我：你觉得哪里用起来方便？哪里不好用？',
      '告诉我：生成的口播稿需要改多少才能用？（不改/改一点/改很多）',
    ],
    goal: '给出真实反馈，我们24小时内优化',
  },
]

const sopText = sop.map(day =>
  `Day${day.day} ${day.title}\n` +
  day.steps.map((s, i) => `${i+1}. ${s}`).join('\n') +
  `\n🎯 目标：${day.goal}`
).join('\n\n')

const disclaimer = [
  { title: '工具定位', content: 'FarmerClaw 仅提供内容运营辅助工具，不承诺销量提升效果，不参与店铺经营，不对平台违规承担责任。' },
  { title: '内容合规', content: '系统已内置三农平台合规检测，但最终上架内容由商家自行审核确认，平台违规责任由商家承担。' },
  { title: '数据安全', content: '商家输入的产品信息仅用于生成内容，不对外披露，不用于训练第三方模型。' },
  { title: '内测协议', content: '内测期间免费使用，结束后需选择付费套餐或停止使用。内测反馈数据用于产品优化。' },
  { title: '服务边界', content: '我们不做代运营、不帮商家发货、不参与价格制定、不对产品质量背书。' },
]

const copy = async (text) => {
  if (!text) return
  await navigator.clipboard.writeText(text).catch(() => {})
  copyToast.value = true
  setTimeout(() => { copyToast.value = false }, 2000)
}
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; display: flex; flex-direction: column; gap: 20px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.section-title { font-size: 15px; font-weight: 800; color: var(--green-dark); display: flex; align-items: center; gap: 8px; }

/* Pricing */
.pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.pricing-card { background: #fff; border: 1px solid var(--border); border-radius: 16px; padding: 24px; position: relative; }
.pricing-card.featured { border: 2px solid var(--green-primary); box-shadow: 0 4px 20px rgba(34,197,94,.15); }
.plan-badge { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: var(--orange-primary); color: #fff; font-size: 11px; font-weight: 700; padding: 3px 12px; border-radius: 99px; white-space: nowrap; }
.plan-name { font-size: 18px; font-weight: 800; color: var(--green-dark); margin-bottom: 12px; }
.plan-price { display: flex; align-items: baseline; gap: 4px; margin-bottom: 4px; }
.price-num { font-size: 36px; font-weight: 900; color: var(--text); }
.price-unit { font-size: 14px; color: var(--text-muted); }
.plan-annual { font-size: 12px; color: var(--green-dark); background: var(--green-bg); padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; }
.plan-target { font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }
.plan-features { list-style: none; display: flex; flex-direction: column; gap: 6px; font-size: 13px; margin-bottom: 16px; padding: 0; }
.plan-cta { font-size: 13px; font-weight: 700; color: var(--orange-primary); background: var(--orange-light); padding: 8px 12px; border-radius: 8px; text-align: center; }

/* Speech */
.tab-row { display: flex; gap: 8px; margin-bottom: 12px; }
.tab-sm { padding: 5px 12px; border: 1px solid var(--border); border-radius: 6px; background: #fff; font-size: 12px; font-weight: 600; cursor: pointer; color: var(--text-muted); }
.tab-sm.active { background: var(--green-primary); color: #fff; border-color: var(--green-primary); }
.speech-box { display: flex; flex-direction: column; gap: 10px; }
.speech-text { background: #f9fafb; border-radius: 8px; padding: 14px; font-size: 13px; line-height: 1.8; white-space: pre-wrap; border: 1px solid var(--border); }
.copy-btn { align-self: flex-end; }

/* SOP */
.sop-card { display: flex; flex-direction: column; gap: 20px; }
.sop-day { border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
.sop-day-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.sop-day-num { background: var(--green-primary); color: #fff; font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 6px; }
.sop-day-title { font-size: 15px; font-weight: 700; }
.sop-steps { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
.sop-step { display: flex; gap: 10px; font-size: 13px; align-items: flex-start; }
.sop-num { width: 20px; height: 20px; background: var(--green-light); color: var(--green-dark); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.sop-goal { font-size: 12px; color: var(--green-dark); font-weight: 600; background: var(--green-bg); padding: 6px 10px; border-radius: 6px; }

/* Disclaimer */
.disclaimer-card { display: flex; flex-direction: column; gap: 12px; }
.disclaimer-item { display: flex; gap: 12px; align-items: flex-start; }
.dis-num { width: 22px; height: 22px; background: var(--text-muted); color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.dis-title { font-size: 13px; font-weight: 700; margin-bottom: 3px; }
.dis-content { font-size: 12px; color: var(--text-muted); line-height: 1.6; }

.copy-toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #f0fdf4; border: 1px solid var(--green-light); color: var(--green-dark); padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 600; z-index: 999; }
</style>
