/**
 * Provider display labels — populated from the backend (providers.yaml).
 * SVG icons live in /static/icons/providers/{key}.svg
 */
import { writable, get } from 'svelte/store';

export const providerLabels = writable({});

/**
 * Populate label store from backend presets or a key→name map.
 * Safe to call multiple times — last write wins.
 */
export function setProviderLabels(labels) {
	if (labels && typeof labels === 'object') {
		providerLabels.set(labels);
	}
}

/**
 * Derive a labels map from _provider_presets returned by GET /api/config.
 * Each preset has a `name` field.
 */
export function setProviderLabelsFromPresets(presets) {
	if (!presets) return;
	const labels = {};
	for (const [k, v] of Object.entries(presets)) {
		labels[k] = v.name || k;
	}
	providerLabels.set(labels);
}

/** Convenience — get label for a key (non-reactive). */
export function getProviderLabel(key) {
	return get(providerLabels)[key] || key;
}
