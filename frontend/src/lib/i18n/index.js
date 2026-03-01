import { writable, derived } from 'svelte/store';
import en from './en.js';
import ru from './ru.js';

/** @type {Record<string, Record<string, string>>} */
const locales = { en, ru };

/** @type {string[]} */
export const availableLocales = Object.keys(locales);

const isBrowser = typeof window !== 'undefined';

function detectLocale() {
	if (!isBrowser) return 'en';
	try {
		const saved = localStorage.getItem('skaro-locale');
		if (saved && locales[saved]) return saved;
	} catch {
		// localStorage may be unavailable (SSR, privacy mode)
	}
	const browser = navigator.language?.slice(0, 2);
	return locales[browser] ? browser : 'en';
}

export const locale = writable(detectLocale());

/** @param {string} loc */
export function setLocale(loc) {
	if (!locales[loc]) return;
	locale.set(loc);
	if (isBrowser) {
		try {
			localStorage.setItem('skaro-locale', loc);
		} catch {
			// Ignore write failures
		}
	}
}

/**
 * Derived store that returns a translation function.
 * Usage in .svelte files: $t('action.implement_stage', { n: 3 })
 */
export const t = derived(locale, ($locale) => {
	/**
	 * @param {string} key
	 * @param {Record<string, string | number>} [params]
	 * @returns {string}
	 */
	return (key, params) => {
		const dict = locales[$locale] || locales.en;
		let text = dict[key] ?? locales.en[key] ?? key;
		if (params) {
			for (const [k, v] of Object.entries(params)) {
				text = text.replaceAll(`{${k}}`, String(v));
			}
		}
		return text;
	};
});
