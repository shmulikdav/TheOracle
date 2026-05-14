<template>
  <div class="world-detail">
    <nav class="navbar">
      <div class="nav-brand" @click="router.push('/')">MIROFISH</div>
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
          <span class="orange-tag">{{ $t('worlds.audience') }}</span>
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

      <!-- New variant chat box -->
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
}

.nav-link.active,
.nav-link:hover {
  color: #fff;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px;
}

.breadcrumb {
  margin-bottom: 24px;
}

.crumb {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #666;
  text-decoration: none;
}

.crumb:hover {
  color: #000;
}

.audience-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border: 1px solid #E5E5E5;
  padding: 32px;
  margin-bottom: 16px;
  gap: 40px;
}

.audience-left {
  flex: 1;
}

.orange-tag {
  display: inline-block;
  background: #FF4500;
  color: #fff;
  padding: 4px 10px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.7rem;
  letter-spacing: 1px;
  margin-bottom: 16px;
}

.audience-title {
  font-size: 2.4rem;
  margin: 0 0 16px 0;
  letter-spacing: -0.5px;
  font-weight: 500;
}

.audience-summary {
  font-size: 1rem;
  color: #555;
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
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #FF4500;
  border: 1px solid #FF4500;
  padding: 2px 8px;
}

.audience-right {
  display: flex;
  gap: 24px;
  flex-shrink: 0;
}

.stat-block {
  text-align: center;
  min-width: 80px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.stat-key {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #666;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.entity-types-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 40px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #666;
}

.entity-types-label {
  margin-right: 4px;
}

.entity-chip {
  background: #F5F5F5;
  padding: 2px 8px;
  color: #000;
}

.variant-composer {
  border: 1px solid #000;
  padding: 28px;
  margin-bottom: 50px;
  background: #FAFAFA;
}

.composer-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.composer-header h2 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
}

.diamond {
  color: #FF4500;
}

.composer-desc {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.6;
}

.composer-input {
  width: 100%;
  border: 1px solid #E5E5E5;
  background: #fff;
  padding: 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  box-sizing: border-box;
}

.composer-input:focus {
  outline: none;
  border-color: #000;
}

.composer-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  gap: 20px;
  flex-wrap: wrap;
}

.plan-preview {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
}

.plan-key {
  color: #999;
  margin-right: 6px;
}

.plan-val {
  color: #000;
}

.run-btn {
  background: #000;
  color: #fff;
  border: none;
  padding: 12px 24px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s;
}

.run-btn:not(:disabled):hover {
  background: #FF4500;
}

.run-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-arrow {
  font-family: sans-serif;
}

.composer-error {
  margin-top: 12px;
  color: #FF4500;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.variants-section {
  margin-top: 30px;
}

.variants-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-bottom: 18px;
}

.variants-header h2 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 500;
}

.variants-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #999;
}

.state-block {
  padding: 40px;
  text-align: center;
  color: #999;
  font-family: 'JetBrains Mono', monospace;
}

.state-block.centered {
  padding-top: 120px;
}

.state-block.error {
  color: #FF4500;
}

.empty-variants {
  padding: 60px 20px;
  border: 1px dashed #E5E5E5;
  text-align: center;
  color: #999;
  font-family: 'JetBrains Mono', monospace;
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
  border: 1px solid #E5E5E5;
  padding: 16px 20px;
  gap: 20px;
}

.variant-row:hover {
  border-color: #000;
}

.variant-left {
  flex: 1;
  min-width: 0;
}

.variant-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  margin-bottom: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #999;
  display: inline-block;
}

.status-dot.running { background: #FF4500; }
.status-dot.done    { background: #2BA84A; }
.status-dot.failed  { background: #B00020; }
.status-dot.idle    { background: #BBB; }

.variant-status {
  font-weight: 700;
  letter-spacing: 0.5px;
}

.variant-id {
  color: #999;
}

.source-pill {
  background: #000;
  color: #fff;
  padding: 2px 8px;
  font-size: 0.65rem;
  letter-spacing: 0.5px;
}

.variant-prompt {
  font-size: 0.9rem;
  color: #333;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.variant-foot {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #999;
  display: flex;
  gap: 14px;
}

.variant-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.link-btn {
  background: transparent;
  border: 1px solid #E5E5E5;
  padding: 8px 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  cursor: pointer;
  color: #000;
}

.link-btn:hover {
  border-color: #000;
}

.link-btn.primary {
  background: #000;
  color: #fff;
  border-color: #000;
}

.link-btn.primary:hover {
  background: #FF4500;
  border-color: #FF4500;
}
</style>
