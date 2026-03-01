/**
 * Format large numbers: 1500 → "1.5k", 2300000 → "2.3M"
 * @param {number} n
 * @returns {string}
 */
export function fmt(n) {
	if (!n) return '0';
	if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
	if (n >= 1_000) return (n / 1_000).toFixed(1) + 'k';
	return n.toLocaleString();
}

/**
 * Sum input + output tokens from a stats entry.
 * @param {{ input_tokens?: number, output_tokens?: number }} obj
 * @returns {number}
 */
export function totalTok(obj) {
	return (obj?.input_tokens || 0) + (obj?.output_tokens || 0);
}

/**
 * Convert { key: { input_tokens, output_tokens, requests } } → sorted array
 * descending by total tokens.
 * @param {Record<string, object>} obj
 * @returns {[string, object][]}
 */
export function sorted(obj) {
	return Object.entries(obj || {}).sort((a, b) => totalTok(b[1]) - totalTok(a[1]));
}
