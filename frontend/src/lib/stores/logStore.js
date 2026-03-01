/**
 * Log and error stores for the Skaro Dashboard.
 *
 * Separated from status so that high-frequency log updates
 * don't trigger re-renders in status-dependent components.
 */
import { writable } from 'svelte/store';

/** @typedef {{ time: string, text: string }} LogEntry */
/** @typedef {{ time: string, text: string, context: string }} ErrorEntry */

/** @type {import('svelte/store').Writable<LogEntry[]>} */
export const logEntries = writable([]);

/** @type {import('svelte/store').Writable<ErrorEntry[]>} */
export const errorEntries = writable([]);

// ── LLM Activity ──

/** Whether an LLM request is currently in progress. */
export const llmActive = writable(false);

/** Phase name of the current LLM request ('architecture', 'devplan', etc). */
export const llmPhase = writable('');

/** Accumulated streaming text from the LLM. */
export const llmText = writable('');

/** @param {string} phase */
export function startLlm(phase) {
	llmActive.set(true);
	llmPhase.set(phase);
	llmText.set('');
}

/** @param {string} text */
export function addLlmChunk(text) {
	llmText.update((t) => t + text);
}

export function endLlm() {
	llmActive.set(false);
}

// ── Regular log/error ──

/** @param {string} text */
export function addLog(text) {
	const time = new Date().toLocaleTimeString();
	logEntries.update((entries) => [{ time, text }, ...entries].slice(0, 50));
}

/**
 * @param {string} text
 * @param {string} [context]
 */
export function addError(text, context = '') {
	const time = new Date().toLocaleTimeString();
	errorEntries.update((entries) => [{ time, text, context }, ...entries].slice(0, 50));
}

export function clearLog() {
	logEntries.set([]);
}

export function clearErrors() {
	errorEntries.set([]);
}
