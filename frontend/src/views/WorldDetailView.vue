<template>
  <div class="world-detail">
    <nav class="navbar">
      <div class="nav-brand" @click="router.push('/')">THE ORACLE</div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">{{ $t('worlds.navHome') }}</router-link>
        <router-link to="/worlds" class="nav-link active">{{ $t('worlds.navFocusGroups') }}</router-link>
        <LanguageSwitcher />
      </div>
    </nav>

    <div class="main-content" v-if="world">
      <div class="breadcrumb">
        <router-link to="/worlds" class="crumb">← {{ $t('worlds.backToLibrary') }}</router-link>
      </div>

      <!-- Audience card -->
      <section class="audience-card">
        <div class="audience-left">
          <span class="oracle-tag">{{ $t('worlds.audience') }}</span>
          <h1 class="audience-title">{{ world.name }}</h1>
          <p class="audience-summary">
            {{ world.audience_summary || world.description || $t('worlds.noSummary') }}
          </p>
          <div v-if="world.tags && world.tags.length" class="tag-row">
            <span v-for="tag in world.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
        <div class="audience-right">
          <div class="stat-block">
            <div class="stat-value">{{ world.profiles_count }}</div>
            <div class="stat-key">{{ $t('worlds.personas') }}</div>
          </div>
          <div class="stat-block">
            <div class="stat-value">{{ (world.entity_types || []).length }}</div>
            <div class="stat-key">{{ $t('worlds.entityTypes') }}</div>
          </div>
          <div class="stat-block">
            <div class="stat-value">{{ world.variant_count }}</div>
            <div class="stat-key">{{ $t('worlds.runs') }}</div>
          </div>
        </div>
      </section>

      <div v-if="(world.entity_types || []).length" class="entity-types-row">
        <span class="entity-types-label">{{ $t('worlds.entityTypes') }}:</span>
        <span v-for="et in world.entity_types" :key="et" class="entity-chip">{{ et }}</span>
      </div>

      <!-- New variant composer -->
      <section class="variant-composer">
        <div class="composer-header">
          <span class="diamond">◇</span>
          <h2>{{ $t('worlds.newVariantTitle') }}</h2>
        </div>
        <p class="composer-desc">{{ $t('worlds.newVariantDesc') }}</p>
        <textarea
          v-model="prompt"
          class="composer-input"
          rows="4"
          :placeholder="$t('worlds.newVariantPlaceholder')"
          :disabled="submitting"
        ></textarea>
        <div class="composer-foot">
          <div class="plan-preview">
            <span class="plan-key">{{ $t('worlds.planLabel') }}</span>
            <span class="plan-val">
              {{ $t('worlds.planValue', {
                world: world.name,
                personas: world.profiles_count
              }) }}
            </span>
          </div>
          <button
            class="run-btn"
            :disabled="!canSubmit"
            @click="submitVariant"
          >
            <span v-if="!submitting">{{ $t('worlds.runVariant') }}</span>
            <span v-else>{{ $t('worlds.creating') }}</span>
            <span class="btn-arrow">→</span>
          </button>
        </div>
        <div v-if="composerError" class="composer-error">{{ composerError }}</div>
      </section>

      <!-- Variants list -->
      <section class="variants-section">
        <header class="variants-header">
          <h2>{{ $t('worlds.variantsTitle') }}</h2>
          <span class="variants-count">{{ variants.length }} {{ $t('worlds.runs') }}</span>
        </header>

        <div v-if="loadingVariants" class="state-block">{{ $t('common.loading') }}</div>

        <div v-else-if="variants.length === 0" class="empty-variants">
          {{ $t('worlds.noVariantsYet') }}
        </div>

        <div v-else class="variants-list">
          <div
            v-for="v in variants"
            :key="v.simulation_id"
            class="variant-row"
          >
            <div class="variant-left">
              <div class="variant-meta">
                <span class="status-dot" :class="statusClass(v)"></span>
                <span class="variant-status">{{ statusLabel(v) }}</span>
                <span class="variant-id">{{ v.simulation_id.slice(0, 14) }}</span>
                <span v-if="v.is_source" class="source-pill">{{ $t('worlds.sourceRun') }}</span>
              </div>
              <div class="variant-prompt" :title="v.prompt">
                {{ v.prompt || $t('worlds.noPrompt') }}
              </div>
              <div class="variant-foot">
                <span class="variant-date">{{ formatDate(v.created_at) }}</span>
                <span v-if="v.total_rounds" class="variant-rounds">
                  {{ v.current_round }}/{{ v.total_rounds }} {{ $t('common.rounds') }}
                </span>
              </div>
            </div>
            <div class="variant-actions">
              <button
                v-if="v.report_id"
                class="link-btn primary"
                @click="router.push(`/report/${v.report_id}`)"
              >
                {{ $t('worlds.viewReport') }} →
              </button>
              <button
                class="link-btn"
                @click="router.push(`/simulation/${v.simulation_id}`)"
              >
                {{ $t('worlds.openRun') }} →
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div v-else-if="loading" class="state-block centered">{{ $t('common.loading') }}</div>
    <div v-else-if="error" class="state-block centered error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getWorld, listWorldVariants, createWorldVariant } from '../api/worlds'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const world = ref(null)
const variants = ref([])
const loading = ref(true)
const loadingVariants = ref(false)
const error = ref('')

const prompt = ref('')
const submitting = ref(false)
const composerError = ref('')

const canSubmit = computed(
  () => prompt.value.trim().length > 0 && !submitting.value && world.value
)

const formatDate = (iso) => {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

const statusClass = (v) => {
  const r = v.runner_status
  if (r === 'running') return 'running'
  if (r === 'completed' || v.status === 'completed') return 'done'
  if (r === 'failed' || v.status === 'failed') return 'failed'
  return 'idle'
}

const statusLabel = (v) => {
  if (v.report_id) return t('worlds.statusReportReady')
  const r = v.runner_status
  if (r === 'running') return t('common.running')
  if (r === 'completed') return t('common.completed')
  if (r === 'failed' || v.status === 'failed') return t('common.failed')
  if (v.status === 'ready') return t('common.ready')
  if (v.status === 'preparing') return t('worlds.statusPreparing')
  return t('common.pending')
}

const loadWorld = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getWorld(route.params.worldId)
    world.value = res.data
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

const loadVariants = async () => {
  loadingVariants.value = true
  try {
    const res = await listWorldVariants(route.params.worldId)
    variants.value = res.data || []
  } catch (e) {
    composerError.value = e.message || String(e)
  } finally {
    loadingVariants.value = false
  }
}

const submitVariant = async () => {
  if (!canSubmit.value) return
  submitting.value = true
  composerError.value = ''
  try {
    const res = await createWorldVariant(route.params.worldId, {
      prompt: prompt.value.trim(),
    })
    const simId = res.data?.simulation_id
    if (simId) {
      router.push(`/simulation/${simId}`)
    }
  } catch (e) {
    composerError.value = e.message || String(e)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadWorld()
  if (world.value) await loadVariants()
})
</script>

<style scoped>
.world-detail {
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
  transition: color 0.2s;
}

.nav-link.active,
.nav-link:hover { color: var(--oracle-gold); }

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px;
}

.breadcrumb { margin-bottom: 24px; }

.crumb {
  font-family: var(--oracle-font-mono);
  font-size: 0.8rem;
  color: var(--oracle-text-muted);
  text-decoration: none;
  transition: color 0.2s;
}

.crumb:hover { color: var(--oracle-gold); }

.audience-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border: 1px solid var(--oracle-border-strong);
  background: var(--oracle-bg-card);
  backdrop-filter: blur(8px);
  padding: 32px;
  margin-bottom: 16px;
  gap: 40px;
  position: relative;
  overflow: hidden;
}

.audience-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(212, 168, 87, 0.06), transparent 50%);
  pointer-events: none;
}

.audience-left { flex: 1; position: relative; }

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
  margin-bottom: 16px;
}

.audience-title {
  font-family: var(--oracle-font-serif), 'Space Grotesk', sans-serif;
  font-size: 2.4rem;
  margin: 0 0 16px 0;
  letter-spacing: -0.5px;
  font-weight: 400;
  color: var(--oracle-text);
}

.audience-summary {
  font-size: 1rem;
  color: var(--oracle-text-dim);
  line-height: 1.7;
  margin: 0 0 16px 0;
  max-width: 720px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  font-family: var(--oracle-font-mono);
  font-size: 0.7rem;
  color: var(--oracle-mystic);
  border: 1px solid rgba(155, 123, 216, 0.4);
  background: rgba(155, 123, 216, 0.08);
  padding: 2px 8px;
}

.audience-right {
  display: flex;
  gap: 24px;
  flex-shrink: 0;
  position: relative;
}

.stat-block {
  text-align: center;
  min-width: 80px;
}

.stat-value {
  font-size: 2.2rem;
  font-weight: 700;
  font-family: var(--oracle-font-mono);
  color: var(--oracle-gold);
  text-shadow: 0 0 24px rgba(212, 168, 87, 0.3);
}

.stat-key {
  font-family: var(--oracle-font-mono);
  font-size: 0.68rem;
  color: var(--oracle-text-muted);
  letter-spacing: 1px;
  text-transform: uppercase;
}

.entity-types-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 40px;
  font-family: var(--oracle-font-mono);
  font-size: 0.78rem;
  color: var(--oracle-text-dim);
}

.entity-types-label {
  margin-right: 4px;
  color: var(--oracle-text-muted);
}

.entity-chip {
  background: var(--oracle-bg-deep);
  border: 1px solid var(--oracle-border);
  padding: 2px 8px;
  color: var(--oracle-text);
}

.variant-composer {
  border: 1px solid var(--oracle-gold);
  padding: 28px;
  margin-bottom: 50px;
  background:
    linear-gradient(135deg, rgba(212, 168, 87, 0.06), rgba(155, 123, 216, 0.04)),
    var(--oracle-bg-card);
  backdrop-filter: blur(10px);
  position: relative;
}

.variant-composer::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px; right: -1px; bottom: -1px;
  background: linear-gradient(135deg, var(--oracle-gold), var(--oracle-mystic), var(--oracle-teal)) border-box;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
          mask-composite: exclude;
  padding: 1px;
  opacity: 0.5;
  pointer-events: none;
}

.composer-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  position: relative;
}

.composer-header h2 {
  margin: 0;
  font-family: var(--oracle-font-serif), 'Space Grotesk', sans-serif;
  font-size: 1.4rem;
  font-weight: 400;
  color: var(--oracle-text);
}

.diamond {
  color: var(--oracle-gold);
  font-size: 1.2rem;
  text-shadow: 0 0 12px var(--oracle-gold);
}

.composer-desc {
  margin: 0 0 16px 0;
  color: var(--oracle-text-dim);
  font-size: 0.9rem;
  line-height: 1.6;
  position: relative;
}

.composer-input {
  width: 100%;
  border: 1px solid var(--oracle-border);
  background: var(--oracle-bg-input);
  color: var(--oracle-text);
  padding: 14px;
  font-family: var(--oracle-font-mono);
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
  position: relative;
}

.composer-input::placeholder { color: var(--oracle-text-muted); }

.composer-input:focus {
  outline: none;
  border-color: var(--oracle-gold);
  box-shadow: 0 0 0 2px rgba(212, 168, 87, 0.15);
}

.composer-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  gap: 20px;
  flex-wrap: wrap;
  position: relative;
}

.plan-preview {
  font-family: var(--oracle-font-mono);
  font-size: 0.75rem;
  color: var(--oracle-text-dim);
}

.plan-key { color: var(--oracle-text-muted); margin-right: 6px; }
.plan-val { color: var(--oracle-text); }

.run-btn {
  background: linear-gradient(135deg, var(--oracle-gold) 0%, #b8924d 100%);
  color: var(--oracle-bg-deep);
  border: none;
  padding: 13px 26px;
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

.run-btn:not(:disabled):hover {
  transform: translateY(-1px);
  filter: brightness(1.1);
  box-shadow: 0 8px 24px rgba(212, 168, 87, 0.4);
}

.run-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.btn-arrow { font-family: sans-serif; }

.composer-error {
  margin-top: 12px;
  color: var(--oracle-rose);
  font-family: var(--oracle-font-mono);
  font-size: 0.8rem;
  position: relative;
}

.variants-section { margin-top: 30px; }

.variants-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-bottom: 18px;
}

.variants-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 400;
  color: var(--oracle-text);
  font-family: var(--oracle-font-serif), 'Space Grotesk', sans-serif;
}

.variants-count {
  font-family: var(--oracle-font-mono);
  font-size: 0.8rem;
  color: var(--oracle-text-muted);
}

.state-block {
  padding: 40px;
  text-align: center;
  color: var(--oracle-text-muted);
  font-family: var(--oracle-font-mono);
}

.state-block.centered { padding-top: 120px; }
.state-block.error { color: var(--oracle-rose); }

.empty-variants {
  padding: 60px 20px;
  border: 1px dashed var(--oracle-border);
  background: var(--oracle-bg-card);
  text-align: center;
  color: var(--oracle-text-muted);
  font-family: var(--oracle-font-mono);
}

.variants-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variant-row {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  border: 1px solid var(--oracle-border);
  background: var(--oracle-bg-card);
  padding: 16px 20px;
  gap: 20px;
  transition: border-color 0.2s, background 0.2s;
}

.variant-row:hover {
  border-color: var(--oracle-gold);
  background: var(--oracle-bg-card-hover);
}

.variant-left { flex: 1; min-width: 0; }

.variant-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--oracle-font-mono);
  font-size: 0.72rem;
  margin-bottom: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--oracle-text-muted);
  display: inline-block;
  box-shadow: 0 0 8px currentColor;
}

.status-dot.running { background: var(--oracle-gold); color: var(--oracle-gold); }
.status-dot.done    { background: var(--oracle-mint); color: var(--oracle-mint); }
.status-dot.failed  { background: var(--oracle-rose); color: var(--oracle-rose); }
.status-dot.idle    { background: var(--oracle-text-muted); box-shadow: none; }

.variant-status {
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--oracle-text);
}

.variant-id { color: var(--oracle-text-muted); }

.source-pill {
  background: var(--oracle-gold);
  color: var(--oracle-bg-deep);
  padding: 2px 8px;
  font-size: 0.62rem;
  letter-spacing: 0.5px;
  font-weight: 700;
}

.variant-prompt {
  font-size: 0.9rem;
  color: var(--oracle-text);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.variant-foot {
  font-family: var(--oracle-font-mono);
  font-size: 0.7rem;
  color: var(--oracle-text-muted);
  display: flex;
  gap: 14px;
}

.variant-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.link-btn {
  background: transparent;
  border: 1px solid var(--oracle-border);
  padding: 8px 14px;
  font-family: var(--oracle-font-mono);
  font-size: 0.72rem;
  cursor: pointer;
  color: var(--oracle-text-dim);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.link-btn:hover {
  border-color: var(--oracle-gold);
  color: var(--oracle-gold);
}

.link-btn.primary {
  background: linear-gradient(135deg, var(--oracle-gold) 0%, #b8924d 100%);
  color: var(--oracle-bg-deep);
  border-color: var(--oracle-gold);
  font-weight: 700;
}

.link-btn.primary:hover {
  filter: brightness(1.1);
  border-color: var(--oracle-gold-bright);
}
</style>
