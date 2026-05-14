<template>
  <div class="worlds-container">
    <nav class="navbar">
      <div class="nav-brand" @click="router.push('/')">MIROFISH</div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">{{ $t('worlds.navHome') }}</router-link>
        <router-link to="/worlds" class="nav-link active">{{ $t('worlds.navFocusGroups') }}</router-link>
        <LanguageSwitcher />
      </div>
    </nav>

    <div class="main-content">
      <header class="page-header">
        <div class="header-left">
          <span class="orange-tag">{{ $t('worlds.tagline') }}</span>
          <h1 class="page-title">{{ $t('worlds.libraryTitle') }}</h1>
          <p class="page-desc">{{ $t('worlds.libraryDesc') }}</p>
        </div>
        <div class="header-right">
          <button class="primary-btn" @click="router.push('/')">
            {{ $t('worlds.buildNew') }} <span class="btn-arrow">→</span>
          </button>
        </div>
      </header>

      <div v-if="loading" class="state-block">{{ $t('common.loading') }}</div>

      <div v-else-if="error" class="state-block error">{{ error }}</div>

      <div v-else-if="worlds.length === 0" class="empty-state">
        <div class="empty-icon">◇</div>
        <h2>{{ $t('worlds.emptyTitle') }}</h2>
        <p>{{ $t('worlds.emptyDesc') }}</p>
        <button class="primary-btn" @click="router.push('/')">
          {{ $t('worlds.buildFirst') }} <span class="btn-arrow">→</span>
        </button>
      </div>

      <div v-else class="worlds-grid">
        <div
          v-for="world in worlds"
          :key="world.world_id"
          class="world-card"
          @click="router.push(`/worlds/${world.world_id}`)"
        >
          <div class="card-meta">
            <span class="meta-id">{{ world.world_id.slice(0, 14) }}</span>
            <span class="meta-runs">{{ world.variant_count }} {{ $t('worlds.runs') }}</span>
          </div>
          <h3 class="card-title">{{ world.name }}</h3>
          <p class="card-summary">{{ world.audience_summary || world.description || $t('worlds.noSummary') }}</p>
          <div class="card-stats">
            <span class="stat-pill">
              <span class="stat-num">{{ world.profiles_count }}</span>
              <span class="stat-label">{{ $t('worlds.personas') }}</span>
            </span>
            <span class="stat-pill">
              <span class="stat-num">{{ (world.entity_types || []).length }}</span>
              <span class="stat-label">{{ $t('worlds.entityTypes') }}</span>
            </span>
          </div>
          <div v-if="world.tags && world.tags.length" class="card-tags">
            <span v-for="tag in world.tags.slice(0, 4)" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <div class="card-footer">
            <span class="footer-date">{{ formatDate(world.created_at) }}</span>
            <span class="footer-cta">{{ $t('worlds.openWorld') }} →</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listWorlds } from '../api/worlds'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const router = useRouter()
const worlds = ref([])
const loading = ref(true)
const error = ref('')

const formatDate = (iso) => {
  if (!iso) return ''
  try {
    return new Date(iso).toISOString().slice(0, 10)
  } catch {
    return iso.slice(0, 10)
  }
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await listWorlds()
    worlds.value = res.data || []
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.worlds-container {
  min-height: 100vh;
  background: #FFFFFF;
  color: #000;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.navbar {
  height: 60px;
  background: #000;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.2rem;
  cursor: pointer;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-link {
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  letter-spacing: 0.5px;
}

.nav-link.active,
.nav-link:hover {
  color: #fff;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 60px 40px;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 50px;
  gap: 40px;
}

.header-left {
  flex: 1;
}

.orange-tag {
  display: inline-block;
  background: #FF4500;
  color: #fff;
  padding: 4px 10px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.75rem;
  letter-spacing: 1px;
  margin-bottom: 20px;
}

.page-title {
  font-size: 3rem;
  margin: 0 0 16px 0;
  letter-spacing: -1px;
  font-weight: 500;
}

.page-desc {
  font-size: 1rem;
  color: #666;
  max-width: 720px;
  line-height: 1.7;
  margin: 0;
}

.primary-btn {
  background: #000;
  color: #fff;
  border: none;
  padding: 14px 28px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  transition: background 0.2s;
}

.primary-btn:hover {
  background: #FF4500;
}

.btn-arrow {
  font-family: sans-serif;
}

.state-block {
  padding: 60px;
  text-align: center;
  color: #999;
  font-family: 'JetBrains Mono', monospace;
}

.state-block.error {
  color: #FF4500;
}

.empty-state {
  text-align: center;
  padding: 100px 40px;
  border: 1px dashed #E5E5E5;
}

.empty-icon {
  color: #FF4500;
  font-size: 3rem;
  margin-bottom: 20px;
}

.empty-state h2 {
  margin: 0 0 12px 0;
  font-size: 1.6rem;
  font-weight: 500;
}

.empty-state p {
  color: #666;
  margin: 0 0 30px 0;
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
}

.worlds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.world-card {
  border: 1px solid #E5E5E5;
  padding: 24px;
  cursor: pointer;
  background: #fff;
  transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
  min-height: 220px;
}

.world-card:hover {
  border-color: #000;
  transform: translateY(-2px);
  box-shadow: 6px 6px 0 0 rgba(0,0,0,0.08);
}

.card-meta {
  display: flex;
  justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #999;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}

.meta-runs {
  color: #FF4500;
  font-weight: 700;
}

.card-title {
  font-size: 1.25rem;
  margin: 0 0 10px 0;
  font-weight: 600;
  letter-spacing: -0.3px;
}

.card-summary {
  font-size: 0.9rem;
  color: #666;
  line-height: 1.5;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.stat-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  background: #F5F5F5;
  padding: 4px 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
}

.stat-num {
  font-weight: 700;
  color: #000;
}

.stat-label {
  color: #666;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

.tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #FF4500;
  border: 1px solid #FF4500;
  padding: 2px 8px;
}

.card-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  padding-top: 14px;
  border-top: 1px solid #F0F0F0;
}

.footer-cta {
  color: #000;
  font-weight: 600;
}
</style>
