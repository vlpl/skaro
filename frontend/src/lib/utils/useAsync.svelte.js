/**
 * Reactive async helper for Svelte 5.
 *
 * Eliminates repeated loading/error state boilerplate.
 *
 * Usage:
 *   const { loading, error, run } = useAsync();
 *   const data = await run(() => api.getSomething());
 *
 * @param {object} [options]
 * @param {(err: Error) => void} [options.onError] — optional error callback (e.g. addError)
 * @returns {{ loading: { value: boolean }, error: { value: string }, run: <T>(fn: () => Promise<T>) => Promise<T|undefined> }}
 */
export function useAsync(options = {}) {
	let loading = $state(false);
	let error = $state('');

	/**
	 * Execute an async function with automatic loading/error state management.
	 * @template T
	 * @param {() => Promise<T>} fn
	 * @returns {Promise<T|undefined>}
	 */
	async function run(fn) {
		loading = true;
		error = '';
		try {
			const result = await fn();
			return result;
		} catch (/** @type {any} */ e) {
			if (e?.name === 'AbortError') return undefined;
			const msg = e?.message || String(e);
			error = msg;
			options.onError?.(e);
			return undefined;
		} finally {
			loading = false;
		}
	}

	return {
		get loading() { return loading; },
		get error() { return error; },
		set error(v) { error = v; },
		run,
	};
}
