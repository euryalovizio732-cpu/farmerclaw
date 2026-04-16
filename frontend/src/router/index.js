import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/login', component: () => import('../views/Login.vue'), meta: { title: '登录', public: true } },
  { path: '/home', component: () => import('../views/Home.vue'), meta: { title: '首页' } },
  { path: '/content-pack', component: () => import('../views/ContentPack.vue'), meta: { title: '今日内容包' } },
  { path: '/pipeline', component: () => import('../views/Pipeline.vue'), meta: { title: '全流程自动化' } },
  { path: '/pain-point', component: () => import('../views/PainPoint.vue'), meta: { title: '痛点挖掘' } },
  { path: '/listing', component: () => import('../views/Listing.vue'), meta: { title: 'Listing生成' } },
  { path: '/dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '数据看板' } },
  { path: '/history', component: () => import('../views/History.vue'), meta: { title: '历史记录' } },
  { path: '/pricing', component: () => import('../views/Pricing.vue'), meta: { title: '内测定价', public: true } },
  { path: '/materials', component: () => import('../views/Materials.vue'), meta: { title: '内测物料', public: true } },
  { path: '/live-review', component: () => import('../views/LiveReview.vue'), meta: { title: '直播复盘' } },
  { path: '/reply', component: () => import('../views/Reply.vue'), meta: { title: '评论回复' } },
  { path: '/ad', component: () => import('../views/AdOptimize.vue'), meta: { title: '投放优化' } },
  { path: '/samples', component: () => import('../views/SampleManager.vue'), meta: { title: '样本库管理' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} — FarmerClaw` : 'FarmerClaw'
})

export default router
