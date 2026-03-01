import { writable } from 'svelte/store';

const STORAGE_KEY = 'skaro-theme';
const VALID_THEMES = ['dark', 'light'];
const isBrowser = typeof window !== 'undefined';

function detectTheme() {
	if (!isBrowser) return 'dark';
	try {
		const saved = localStorage.getItem(STORAGE_KEY);
		if (saved && VALID_THEMES.includes(saved)) return saved;
	} catch {
		// localStorage may be unavailable
	}
	return 'dark';
}

export const theme = writable(detectTheme());

/** @param {string} value */
export function setTheme(value) {
	if (!VALID_THEMES.includes(value)) return;
	theme.set(value);
	if (isBrowser) {
		try {
			localStorage.setItem(STORAGE_KEY, value);
		} catch {
			// Ignore write failures
		}
		applyTheme(value);
	}
}

/** Apply data-theme attribute to <html> for CSS variable switching. */
export function applyTheme(value) {
	if (!isBrowser) return;
	document.documentElement.setAttribute('data-theme', value);
}
