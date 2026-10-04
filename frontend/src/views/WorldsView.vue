<template>
  <div class="worlds-container">
    <nav class="navbar">
      <div class="nav-brand" @click="router.push('/')">THE ORACLE</div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">{{ $t('worlds.navHome') }}</router-link>
        <router-link to="/worlds" class="nav-link active">{{ $t('worlds.navFocusGroups') }}</router-link>
        <LanguageSwitcher />
      </div>
    </nav>

    <div class="main-content">
      <header class="page-header">
        <div class="header-left">
          <span class="oracle-tag">{{ $t('worlds.tagline') }}</span>
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
  background: transparent;
  color: var(--oracle-text);
  font-family: var(--oracle-font-sans);
  position: relative;
  z-index: 1;
}

.navbar {
  height: 60px;
  background: rgba(11, 8, 32, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--oracle-border);
  color: var(--oracle-text);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: var(--oracle-font-mono);
  font-weight: 700;
  letter-spacing: 2px;
  font-size: 1.05rem;
  cursor: pointer;
  color: var(--oracle-text);
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.nav-brand::before {
  content: '✦';
  color: var(--oracle-gold);
  text-shadow: 0 0 12px var(--oracle-gold);
}

.nav-brand:hover { color: var(--oracle-gold-bright); }

.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-link {
  color: var(--oracle-text-dim);
  text-decoration: none;
  font-family: var(--oracle-font-mono);
  font-size: 0.85rem;
  letter-spacing: 0.5px;
  transition: color 0.2s;
}

.nav-link.active,
.nav-link:hover {
  color: var(--oracle-gold);
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

.header-left { flex: 1; }

.oracle-tag {
  display: inline-block;
  font-family: var(--oracle-font-mono);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--oracle-gold);
  padding: 4px 10px;
  border: 1px solid var(--oracle-border-strong);
  background: rgba(212, 168, 87, 0.06);
  text-transform: uppercase;
  margin-bottom: 20px;
}

.page-title {
  font-family: var(--oracle-font-serif), 'Space Grotesk', sans-serif;
  font-size: 3rem;
  margin: 0 0 16px 0;
  letter-spacing: -0.5px;
  font-weight: 400;
  color: var(--oracle-text);
}

.page-desc {
  font-size: 0.95rem;
  color: var(--oracle-text-dim);
  max-width: 720px;
  line-height: 1.7;
  margin: 0;
}

.primary-btn {
  background: linear-gradient(135deg, var(--oracle-gold) 0%, #b8924d 100%);
  color: var(--oracle-bg-deep);
  border: none;
  padding: 14px 28px;
  font-family: var(--oracle-font-mono);
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  transition: transform 0.15s, box-shadow 0.2s, filter 0.2s;
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(212, 168, 87, 0.35);
  filter: brightness(1.08);
}

.btn-arrow { font-family: sans-serif; }

.state-block {
  padding: 60px;
  text-align: center;
  color: var(--oracle-text-muted);
  font-family: var(--oracle-font-mono);
}

.state-block.error { color: var(--oracle-rose); }

.empty-state {
  text-align: center;
  padding: 100px 40px;
  border: 1px dashed var(--oracle-border-strong);
  background: var(--oracle-bg-card);
}

.empty-icon {
  color: var(--oracle-gold);
  font-size: 3rem;
  margin-bottom: 20px;
  text-shadow: 0 0 24px rgba(212, 168, 87, 0.4);
}

.empty-state h2 {
  margin: 0 0 12px 0;
  font-size: 1.6rem;
  font-weight: 400;
  font-family: var(--oracle-font-serif), 'Space Grotesk', sans-serif;
  color: var(--oracle-text);
}

.empty-state p {
  color: var(--oracle-text-dim);
  margin: 0 auto 30px;
  max-width: 480px;
  line-height: 1.6;
}

.worlds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.world-card {
  border: 1px solid var(--oracle-border);
  padding: 24px;
  cursor: pointer;
  background: var(--oracle-bg-card);
  backdrop-filter: blur(8px);
  transition: transform 0.18s, border-color 0.18s, box-shadow 0.18s, background 0.18s;
  display: flex;
  flex-direction: column;
  min-height: 220px;
  position: relative;
}

.world-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(212, 168, 87, 0.08), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.world-card:hover {
  border-color: var(--oracle-gold);
  transform: translateY(-3px);
  background: var(--oracle-bg-card-hover);
  box-shadow: 0 12px 40px rgba(11, 8, 32, 0.6), 0 0 0 1px rgba(212, 168, 87, 0.2);
}

.world-card:hover::before { opacity: 1; }

.card-meta {
  display: flex;
  justify-content: space-between;
  font-family: var(--oracle-font-mono);
  font-size: 0.7rem;
  color: var(--oracle-text-muted);
  letter-spacing: 0.5px;
  margin-bottom: 16px;
  position: relative;
}

.meta-runs {
  color: var(--oracle-gold);
  font-weight: 700;
}

.card-title {
  font-size: 1.3rem;
  margin: 0 0 10px 0;
  font-weight: 500;
  letter-spacing: -0.3px;
  color: var(--oracle-text);
  font-family: var(--oracle-font-serif), 'Space Grotesk', sans-serif;
  position: relative;
}

.card-summary {
  font-size: 0.88rem;
  color: var(--oracle-text-dim);
  line-height: 1.55;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  position: relative;
}

.card-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  position: relative;
}

.stat-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  background: var(--oracle-bg-deep);
  border: 1px solid var(--oracle-border);
  padding: 4px 10px;
  font-family: var(--oracle-font-mono);
  font-size: 0.72rem;
}

.stat-num {
  font-weight: 700;
  color: var(--oracle-gold);
}

.stat-label { color: var(--oracle-text-muted); }

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
  position: relative;
}

.tag {
  font-family: var(--oracle-font-mono);
  font-size: 0.68rem;
  color: var(--oracle-mystic);
  border: 1px solid rgba(155, 123, 216, 0.4);
  padding: 2px 8px;
  background: rgba(155, 123, 216, 0.08);
}

.card-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: var(--oracle-font-mono);
  font-size: 0.72rem;
  color: var(--oracle-text-muted);
  padding-top: 14px;
  border-top: 1px solid var(--oracle-border);
  position: relative;
}

.footer-cta {
  color: var(--oracle-gold);
  font-weight: 600;
}
</style>
