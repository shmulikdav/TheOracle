import service, { requestWithRetry } from './index'

/**
 * List all Worlds (saved synthetic audiences) with derived stats.
 */
export const listWorlds = () => service.get('/api/worlds')

/**
 * Create a World from an existing project + simulation.
 * @param {Object} data - { name, description, audience_summary, project_id, simulation_id?, tags? }
 */
export const createWorld = (data) =>
  requestWithRetry(() => service.post('/api/worlds', data), 3, 1000)

/**
 * Get a single World by id.
 */
export const getWorld = (worldId) => service.get(`/api/worlds/${worldId}`)

/**
 * Update editable fields on a World.
 * @param {Object} data - any of { name, description, audience_summary, tags }
 */
export const updateWorld = (worldId, data) =>
  service.patch(`/api/worlds/${worldId}`, data)

/**
 * Delete a World (does not delete the underlying project / graph).
 */
export const deleteWorld = (worldId) => service.delete(`/api/worlds/${worldId}`)

/**
 * List variant runs (simulations) attached to a World.
 */
export const listWorldVariants = (worldId) =>
  service.get(`/api/worlds/${worldId}/variants`)

/**
 * Kick off a new variant run against a World. Reuses the World's graph + personas.
 * @param {Object} data - { prompt, enable_twitter?, enable_reddit? }
 */
export const createWorldVariant = (worldId, data) =>
  requestWithRetry(() => service.post(`/api/worlds/${worldId}/variants`, data), 3, 1000)
