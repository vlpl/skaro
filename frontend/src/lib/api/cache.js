/**
 * Simple TTL cache for API responses.
 *
 * Prevents redundant network requests when multiple components
 * request the same data within a short time window.
 *
 * Usage:
 *   import { cachedFetch, invalidate } from '$lib/api/cache.js';
 *
 *   // Returns cached data if fresh, otherwise fetches
 *   const data = await cachedFetch('status', () => api.getStatus());
 *
 *   // After a mutation, invalidate related cache keys
 *   invalidate('status');
 *   invalidate('architecture');
 */

/** @typedef {{ data: any, ts: number }} CacheEntry */

/** @type {Map<string, CacheEntry>} */
const cache = new Map();

/** @type {Map<string, Promise<any>>} */
const inflight = new Map();

/** Default TTL in milliseconds (10 seconds). */
const DEFAULT_TTL = 10_000;

/**
 * Fetch data with caching and request deduplication.
 *
 * - If a cached entry exists and is within TTL, returns it immediately.
 * - If the same key is already being fetched, returns the in-flight promise
 *   (prevents duplicate concurrent requests).
 * - Otherwise, calls `fetchFn`, caches the result, and returns it.
 *
 * @template T
 * @param {string} key — unique cache key (e.g. 'status', 'architecture')
 * @param {() => Promise<T>} fetchFn — the API call to execute
 * @param {number} [ttl] — time-to-live in ms (default: 10 000)
 * @returns {Promise<T>}
 */
export async function cachedFetch(key, fetchFn, ttl = DEFAULT_TTL) {
	// 1. Check cache
	const entry = cache.get(key);
	if (entry && (Date.now() - entry.ts) < ttl) {
		return entry.data;
	}

	// 2. Deduplicate in-flight requests
	const existing = inflight.get(key);
	if (existing) {
		return existing;
	}

	// 3. Fetch, cache, return
	const promise = fetchFn().then((data) => {
		cache.set(key, { data, ts: Date.now() });
		inflight.delete(key);
		return data;
	}).catch((err) => {
		inflight.delete(key);
		throw err;
	});

	inflight.set(key, promise);
	return promise;
}

/**
 * Invalidate one or more cache keys.
 * Call after mutations to ensure next read fetches fresh data.
 *
 * @param {...string} keys — cache keys to invalidate
 */
export function invalidate(...keys) {
	for (const key of keys) {
		cache.delete(key);
	}
}

/**
 * Invalidate all cache entries.
 */
export function invalidateAll() {
	cache.clear();
}
