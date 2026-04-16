<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">📦 样本库管理</h1>
      <p class="page-desc">查看、导入、审核 Few-shot 样本，填充越多生成质量越高</p>
    </div>

    <div class="page-body">
      <!-- 统计 -->
      <div class="stats-row" v-if="statsData">
        <div class="stat-card">
          <div class="stat-val">{{ statsData.total_samples }}</div>
          <div class="stat-lbl">样本总量</div>
        </div>
        <div class="stat-card">
          <div class="stat-val good">{{ statsData.validated_samples }}</div>
          <div class="stat-lbl">已验证</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">{{ statsData.categories_with_samples }}</div>
          <div class="stat-lbl">有样本品类</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" :class="statsData.is_ready ? 'good' : 'warn'">
            {{ statsData.is_ready ? '已就绪' : '待填充' }}
          </div>
          <div class="stat-lbl">Few-shot 状态</div>
        </div>
      </div>

      <!-- 操作区 -->
      <div class="card">
        <div class="ops-row">
          <div class="filter-group">
            <select v-model="filterCat" class="form-select" @change="loadSamples">
              <option value="">全部品类</option>
              <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
            </select>
            <select v-model="filterType" class="form-select" @change="loadSamples">
              <option value="script">口播文本</option>
              <option value="topic">选题标题</option>
              <option value="live_module">直播话术</option>
              <option value="pain_point">痛点分析</option>
              <option value="reply">客服回复</option>
            </select>
          </div>

          <div class="action-group">
            <button class="btn btn-secondary" @click="showAddModal = true">+ 手动添加</button>
            <label class="btn btn-primary import-btn">
              📁 导入 JSON
              <input type="file" accept=".json" @change="handleImport" hidden />
            </label>
          </div>
        </div>
      </div>

      <!-- 样本列表 -->
      <div class="card">
        <h3 class="card-title">
          样本列表（{{ samples.length }} 条）
          <span class="badge badge-green" v-if="filterCat">{{ filterCat }}</span>
          <span class="badge badge-gray">{{ typeLabel[filterType] || filterType }}</span>
        </h3>

        <div v-if="samples.length" class="sample-list">
          <div v-for="s in samples" :key="s.id" class="sample-item">
            <div class="si-header">
              <span class="si-cat badge badge-green">{{ s.category }}</span>
              <span class="si-hook" v-if="s.hook_type">{{ s.hook_type }}</span>
              <span class="si-source">{{ s.source || '未知来源' }}</span>
              <span :class="['si-status', s.usable_direct ? 'verified' : 'pending']">
                {{ s.usable_direct ? '✅ 已验证' : '⏳ 待验证' }}
              </span>
            </div>
            <div class="si-text">{{ s.script || s.title || s.text || '(空)' }}</div>
            <div class="si-footer">
              <span v-if="s.views_approx" class="si-views">{{ s.views_approx }} 播放</span>
              <span class="si-type-badge">{{ s.source_type === 'validated' ? '商家反馈' : '基础库' }}</span>
            </div>
          </div>
        </div>
        <div v-else class="empty">暂无样本，请导入或手动添加</div>
      </div>

      <!-- 添加弹窗 -->
      <div class="modal-overlay" v-if="showAddModal" @click.self="showAddModal = false">
        <div class="modal">
          <h3 class="modal-title">手动添加样本</h3>
          <div class="form-group">
            <label class="form-label">品类</label>
            <select v-model="addForm.category" class="form-select">
              <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">类型</label>
            <select v-model="addForm.sample_type" class="form-select">
              <option value="script">口播文本</option>
              <option value="topic">选题标题</option>
              <option value="live_module">直播话术</option>
              <option value="pain_point">痛点分析</option>
              <option value="reply">客服回复</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">内容</label>
            <textarea v-model="addForm.script" class="form-textarea" rows="5" placeholder="粘贴口播文本 / 选题标题 / 话术内容..."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">钩子类型</label>
              <input v-model="addForm.hook_type" class="form-input" placeholder="价格冲击 / 知识反问 / ..." />
            </div>
            <div class="form-group">
              <label class="form-label">来源</label>
              <input v-model="addForm.source" class="form-input" placeholder="抖音@xxx / 手动采集" />
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
            <button class="btn btn-primary" @click="submitAdd" :disabled="!addForm.script">确认添加</button>
          </div>
        </div>
      </div>

      <!-- Toast -->
      <div class="toast" v-if="toast">{{ toast }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { sampleApi } from '../api/index.js'

const categories = ref([])
const samples = ref([])
const statsData = ref(null)
const filterCat = ref('')
const filterType = ref('script')
const showAddModal = ref(false)
const toast = ref('')

const typeLabel = {
  script: '口播文本',
  topic: '选题标题',
  live_module: '直播话术',
  pain_point: '痛点分析',
  reply: '客服回复',
}

const addForm = ref({
  category: '脐橙',
  sample_type: 'script',
  script: '',
  hook_type: '',
  source: '',
})

const showToast = (msg) => {
  toast.value = msg
  setTimeout(() => toast.value = '', 2500)
}

const loadStats = async () => {
  try {
    const res = await sampleApi.stats()
    if (res.code === 0) statsData.value = res.data
  } catch {}
}

const loadCategories = async () => {
  try {
    const res = await sampleApi.categories()
    if (res.code === 0) categories.value = res.data
  } catch {}
}

const loadSamples = async () => {
  try {
    const res = await sampleApi.list({ category: filterCat.value, sample_type: filterType.value })
    if (res.code === 0) samples.value = res.data.samples || []
  } catch {}
}

const submitAdd = async () => {
  try {
    const res = await sampleApi.add(addForm.value)
    if (res.code === 0) {
      showToast(res.message || '添加成功')
      showAddModal.value = false
      addForm.value.script = ''
      await loadSamples()
      await loadStats()
    } else {
      showToast(res.message || '添加失败')
    }
  } catch (e) {
    showToast('请求失败: ' + e.message)
  }
}

const handleImport = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  const cat = filterCat.value || prompt('请输入品类名称（如：脐橙）')
  if (!cat) return
  const fd = new FormData()
  fd.append('file', file)
  fd.append('category', cat)
  fd.append('sample_type', filterType.value)
  try {
    const res = await sampleApi.importFile(fd)
    showToast(res.message || `导入完成`)
    await loadSamples()
    await loadStats()
  } catch (err) {
    showToast('导入失败: ' + err.message)
  }
  e.target.value = ''
}

onMounted(async () => {
  await Promise.all([loadStats(), loadCategories()])
  await loadSamples()
})
</script>

<style scoped>
.page { min-height: 100vh; }
.page-body { padding: 0 32px 32px; display: flex; flex-direction: column; gap: 14px; }
.card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.card-title { font-size: 15px; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat-card { background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 16px; text-align: center; }
.stat-val { font-size: 26px; font-weight: 800; color: var(--text); }
.stat-val.good { color: var(--green-dark); }
.stat-val.warn { color: #c2410c; }
.stat-lbl { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

.ops-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.filter-group { display: flex; gap: 8px; }
.action-group { display: flex; gap: 8px; }
.import-btn { cursor: pointer; }

.sample-list { display: flex; flex-direction: column; gap: 10px; }
.sample-item { border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
.si-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.si-cat { font-size: 11px; }
.si-hook { font-size: 11px; background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 4px; }
.si-source { font-size: 11px; color: var(--text-muted); }
.si-status { font-size: 11px; margin-left: auto; font-weight: 600; }
.si-status.verified { color: var(--green-dark); }
.si-status.pending { color: #92400e; }
.si-text { font-size: 13px; line-height: 1.7; color: var(--text); white-space: pre-wrap; max-height: 120px; overflow-y: auto; }
.si-footer { display: flex; gap: 8px; margin-top: 8px; font-size: 11px; color: var(--text-muted); }
.si-views { background: #f3f4f6; padding: 2px 8px; border-radius: 4px; }
.si-type-badge { background: var(--green-bg); color: var(--green-dark); padding: 2px 8px; border-radius: 4px; }

.empty { text-align: center; color: var(--text-muted); padding: 40px 0; font-size: 14px; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.4); z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 14px; padding: 24px; width: 480px; max-width: 90vw; max-height: 90vh; overflow-y: auto; }
.modal-title { font-size: 16px; font-weight: 700; margin-bottom: 16px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }

.toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  background: #f0fdf4; border: 1px solid var(--green-light); color: var(--green-dark);
  padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 600;
  z-index: 999; box-shadow: var(--shadow-md);
}
</style>
