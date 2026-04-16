<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">📁 内测物料</h1>
      <p class="page-desc">服务协议 · 邀约话术 · 3天上手SOP — 可直接复制使用</p>
    </div>

    <div class="page-body">
      <!-- Tab 导航 -->
      <div class="tab-nav">
        <button v-for="tab in tabs" :key="tab.id"
          :class="['tab-btn', activeTab === tab.id ? 'active' : '']"
          @click="activeTab = tab.id">
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab 1：邀约话术 -->
      <div v-if="activeTab === 'invite'">
        <div class="card">
          <div class="card-title-row">
            <h3 class="card-title">📱 微信群发版（简短，适合批量触达）</h3>
            <button class="btn-copy" @click="copy(wechatBroadcast)">复制话术</button>
          </div>
          <div class="script-box">{{ wechatBroadcast }}</div>
        </div>

        <div class="card">
          <div class="card-title-row">
            <h3 class="card-title">💬 1v1 私信版（有温度，转化更高）</h3>
            <button class="btn-copy" @click="copy(wechat1v1)">复制话术</button>
          </div>
          <div class="script-box">{{ wechat1v1 }}</div>
        </div>

        <div class="card">
          <div class="card-title-row">
            <h3 class="card-title">🤝 跟进话术（3天后追问）</h3>
            <button class="btn-copy" @click="copy(followUp)">复制话术</button>
          </div>
          <div class="script-box">{{ followUp }}</div>
        </div>

        <div class="card tip-card">
          <h3 class="card-title">📌 邀约注意事项</h3>
          <ul class="tip-list">
            <li v-for="tip in inviteTips" :key="tip">{{ tip }}</li>
          </ul>
        </div>
      </div>

      <!-- Tab 2：服务协议 -->
      <div v-if="activeTab === 'agreement'">
        <div class="card">
          <div class="card-title-row">
            <h3 class="card-title">📄 内测服务协议（精简版，微信截图可用）</h3>
            <button class="btn-copy" @click="copy(agreement)">复制协议</button>
          </div>
          <div class="agreement-box" v-html="agreementHtml"></div>
        </div>

        <div class="card tip-card">
          <h3 class="card-title">⚠️ 协议说明</h3>
          <ul class="tip-list">
            <li>内测阶段免费使用，但需要商家提供使用反馈</li>
            <li>AI 生成内容仅供参考，商家使用前应自行判断合规性</li>
            <li>不承诺提升销量，工具效果因商家内容质量而异</li>
            <li>内测结束后正式版采用订阅制，价格见定价页</li>
          </ul>
        </div>
      </div>

      <!-- Tab 3：3天SOP -->
      <div v-if="activeTab === 'sop'">
        <div class="sop-intro card">
          <strong>使用场景：</strong>发给新内测用户，帮助他们 3 天内完整体验产品并给出有效反馈。建议配合截图/视频说明发送。
        </div>

        <div v-for="(day, i) in sopDays" :key="i" class="card sop-day">
          <div class="day-header">
            <span class="day-badge">Day {{ i + 1 }}</span>
            <span class="day-title">{{ day.title }}</span>
          </div>
          <div class="step-list">
            <div v-for="(step, j) in day.steps" :key="j" class="step-item">
              <span class="step-num">{{ j + 1 }}</span>
              <div class="step-content">
                <div class="step-action">{{ step.action }}</div>
                <div class="step-detail" v-if="step.detail">{{ step.detail }}</div>
              </div>
            </div>
          </div>
          <div class="day-goal">🎯 今日目标：{{ day.goal }}</div>
          <div class="card-title-row" style="margin-top:12px">
            <div></div>
            <button class="btn-copy" @click="copy(dayText(day, i+1))">复制当日SOP</button>
          </div>
        </div>

        <div class="card">
          <div class="card-title-row">
            <h3 class="card-title">📊 反馈收集问题（Day7发送）</h3>
            <button class="btn-copy" @click="copy(feedbackQuestions)">复制问题</button>
          </div>
          <div class="script-box">{{ feedbackQuestions }}</div>
        </div>
      </div>
    </div>

    <div class="copy-toast" v-if="copyToast">✅ 已复制到剪贴板</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeTab = ref('invite')
const copyToast = ref(false)

const tabs = [
  { id: 'invite', label: '📱 邀约话术' },
  { id: 'agreement', label: '📄 服务协议' },
  { id: 'sop', label: '📋 3天上手SOP' },
]

// ── 邀约话术 ─────────────────────────────────────────
const wechatBroadcast = `老板你好！我在做一个专门给抖音三农商家用的AI工具，可以帮你每天自动生成：视频选题+口播稿+直播话术，3分钟搞定，完全不用写稿子。

现在在做免费内测，想邀请你来体验一下，用完帮我说说效果怎么样就行。感兴趣的话告诉我，我发你注册链接！`

const wechat1v1 = `[老板名字]你好，我是[你的名字]。

看你在抖音卖[品类]，每天要发视频+直播，内容这块应该挺累的吧？

我最近做了个专门给三农商家用的AI工具——你输入今天要卖什么，系统3分钟自动给你出：
• 3条视频选题（含拍摄建议）
• 3条完整口播稿（30秒，可以直接念）
• 今天的直播话术（模块化，不会冷场）

现在在做免费内测，不收费，就是需要你用完告诉我哪里不好用。

感觉有用的话可以试试，我直接发你注册链接？`

const followUp = `[老板名字]你好，上次给你发的AI工具试了吗？

主要是想知道生成的口播稿能不能直接用，还是需要改很多？这个对我改进产品很重要。

如果还没试，我可以帮你直接操作一遍，15分钟搞定，你看什么时候方便？`

const inviteTips = [
  '优先找月销5-50万、自己在播的商家，有痛点才有动力用',
  '群发版效果差，1v1 版转化率高 3-5 倍，值得花时间写',
  '不要说「免费」，要说「内测名额有限」，制造稀缺感',
  '第一批内测控制在 5-10 家，太多了跟不过来',
  '邀约后第二天主动问进度，不问基本就废了',
]

// ── 服务协议 ─────────────────────────────────────────
const agreement = `FarmerClaw 三农AI工具 · 内测服务协议

一、服务内容
FarmerClaw 为您提供抖音三农电商内容自动化 AI 工具，包括：视频选题生成、口播稿生成、直播话术生成等功能。

二、内测条款
1. 内测期间免费使用，内测结束后将推出付费版本。
2. 您同意在使用过程中提供真实反馈，包括但不限于：生成内容质量评价、使用频次、具体改进建议。
3. 内测资格不可转让，仅限本人使用。

三、免责声明
1. AI 生成内容仅供参考，商家应在使用前自行判断内容的准确性和合规性。
2. 本工具不承诺提升销量或直播效果，具体成效取决于商家的实际执行质量。
3. 本工具不会收集或存储您的产品定价、商业机密等敏感信息。

四、终止条款
您可随时停止使用本服务。若发现滥用行为（如批量导出、转售内容等），我们有权终止内测资格。

如您同意以上条款，请回复「同意」，我即发送注册链接。`

const agreementHtml = agreement.replace(/\n/g, '<br>').replace(/一、|二、|三、|四、/g, '<strong>$&</strong>')

// ── 3天SOP ───────────────────────────────────────────
const sopDays = [
  {
    title: '注册 + 生成第一个内容包',
    goal: '成功生成今日内容包，并选出1条口播稿实际拍摄',
    steps: [
      { action: '打开注册链接，填写邮箱+密码完成注册', detail: '注册后直接进入主页，不需要审核' },
      { action: '点击「今日内容包」，填写产品信息', detail: '产品名/品类必填，产地和价格选填，越详细效果越好' },
      { action: '点击生成，等待约30秒', detail: 'AI会生成：3个选题、3条口播稿、直播话术模块' },
      { action: '找一条你觉得最合适的口播稿，今天拍一条视频', detail: '可以在口播稿旁边点复制，粘贴到备忘录对着念' },
    ],
  },
  {
    title: '连续使用 + 对比效果',
    goal: '连续使用第2天，感受与自己写稿的差异，标注修改了哪里',
    steps: [
      { action: '重新打开「今日内容包」，换一个品类/产品试试', detail: '看看不同产品的生成效果差异' },
      { action: '把生成的话术和你自己平时用的话术对比', detail: '重点看：哪句话说出来更顺口？哪里不像你的风格？' },
      { action: '在备忘录记录下来：哪里改了，改成什么', detail: '这个对我改进AI很有帮助，哪怕一两句话也行' },
      { action: '如果有直播，用「直播话术」模块里的一段话试试', detail: '看看观众反应是否有变化' },
    ],
  },
  {
    title: '反馈 + 深度体验',
    goal: '给出一份有效反馈，告诉我哪里最有用、哪里最难用',
    steps: [
      { action: '打开「痛点挖掘」功能，输入你的品类看看', detail: '这个功能会分析你的竞争对手在哪里有痛点' },
      { action: '如果有新视频数据（播放量/完播率），试试「投放优化」', detail: '会告诉你这条视频值不值得花钱投DOU+' },
      { action: '把3天体验写成3-5句话发给我', detail: '重点：口播稿能直接用吗？哪里最省时间？哪里需要改进？' },
    ],
  },
]

const dayText = (day, num) => {
  const lines = [`【Day${num}：${day.title}】\n`]
  day.steps.forEach((s, i) => {
    lines.push(`${i + 1}. ${s.action}`)
    if (s.detail) lines.push(`   💡 ${s.detail}`)
  })
  lines.push(`\n🎯 今日目标：${day.goal}`)
  return lines.join('\n')
}

const feedbackQuestions = `[老板名字]你好！用了3天了，帮我回答几个问题，5分钟就好：

1. 生成的口播稿，你直接用的比例大概是多少？
   □ 80%以上可以直接用  □ 50%-80%，改一点  □ 50%以下，改很多  □ 基本不能用

2. 最省时间的功能是哪个？（可多选）
   □ 视频选题  □ 口播稿  □ 直播话术  □ 痛点分析  □ 投放建议

3. 最需要改进的是什么？（直接说，越直白越好）
   答：

4. 你每天用的频率是？
   □ 每天都用  □ 2-3天用一次  □ 偶尔用  □ 基本没用

5. 你愿意每月花多少钱订阅这个工具？（基于你的实际体验）
   □ 不愿意付费  □ 100元以内  □ 200-500元  □ 500元以上

6. 你会推荐给同行用吗？打分 0-10 分：___分

谢谢！等正式版上线了给你整个优惠 🙏`

// ── Copy ──────────────────────────────────────────────
const copy = async (text) => {
  await navigator.clipboard.writeText(text).catch(() => {})
  copyToast.value = true
  setTimeout(() => copyToast.value = false, 2500)
}
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; display: flex; flex-direction: column; gap: 14px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.card-title { font-size: 15px; font-weight: 700; margin-bottom: 0; }
.card-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }

/* Tabs */
.tab-nav { display: flex; gap: 8px; }
.tab-btn { padding: 8px 18px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; background: #fff; color: var(--text-muted); }
.tab-btn.active { background: var(--green-primary); color: #fff; border-color: var(--green-primary); }

/* Script */
.script-box {
  background: #f9fafb; border-radius: 8px; padding: 16px;
  font-size: 13px; line-height: 1.8; white-space: pre-wrap; color: var(--text);
}

/* Agreement */
.agreement-box {
  background: #f9fafb; border-radius: 8px; padding: 16px;
  font-size: 13px; line-height: 2; color: var(--text);
}

/* Tips */
.tip-card { border-color: #fde68a; background: #fffbeb; }
.tip-list { list-style: none; display: flex; flex-direction: column; gap: 6px; padding: 0; margin: 0; }
.tip-list li { font-size: 13px; color: #92400e; padding-left: 16px; position: relative; }
.tip-list li::before { content: '•'; position: absolute; left: 0; }

/* SOP */
.sop-intro { font-size: 13px; color: var(--text-muted); padding: 14px 16px; }
.sop-day { }
.day-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.day-badge { background: var(--green-primary); color: #fff; font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 6px; }
.day-title { font-size: 15px; font-weight: 700; }
.step-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.step-item { display: flex; gap: 12px; align-items: flex-start; }
.step-num { background: var(--green-bg); color: var(--green-dark); font-size: 12px; font-weight: 800; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px; }
.step-content { flex: 1; }
.step-action { font-size: 13px; font-weight: 600; line-height: 1.5; }
.step-detail { font-size: 12px; color: var(--text-muted); margin-top: 2px; line-height: 1.5; }
.day-goal { font-size: 13px; font-weight: 700; color: var(--green-dark); background: var(--green-bg); padding: 8px 12px; border-radius: 6px; }

.btn-copy { font-size: 12px; padding: 5px 14px; background: var(--green-primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; }
.btn-copy:hover { background: var(--green-dark); }

.copy-toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #f0fdf4; border: 1px solid var(--green-light); color: var(--green-dark); padding: 10px 24px; border-radius: 8px; font-size: 13px; font-weight: 600; z-index: 999; }
</style>
