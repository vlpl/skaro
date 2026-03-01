/**
 * Markdown tag insertion utilities.
 * All functions operate on a textarea element and return
 * { value, selectionStart, selectionEnd } to apply.
 */

/**
 * Wrap the current selection with before/after strings.
 * If nothing is selected, inserts `before + placeholder + after` and selects placeholder.
 * @param {HTMLTextAreaElement} el
 * @param {string} before
 * @param {string} after
 * @param {string} [placeholder='text']
 * @returns {{ value: string, selectionStart: number, selectionEnd: number }}
 */
export function wrapSelection(el, before, after, placeholder = 'text') {
	const { value, selectionStart: s, selectionEnd: e } = el;
	const selected = value.slice(s, e);

	if (selected) {
		const wrapped = before + selected + after;
		return {
			value: value.slice(0, s) + wrapped + value.slice(e),
			selectionStart: s + before.length,
			selectionEnd: s + before.length + selected.length,
		};
	}

	const inserted = before + placeholder + after;
	return {
		value: value.slice(0, s) + inserted + value.slice(e),
		selectionStart: s + before.length,
		selectionEnd: s + before.length + placeholder.length,
	};
}

/**
 * Add a prefix to the beginning of each selected line (or current line if no selection).
 * @param {HTMLTextAreaElement} el
 * @param {string} prefix
 * @returns {{ value: string, selectionStart: number, selectionEnd: number }}
 */
export function prefixLine(el, prefix) {
	const { value, selectionStart: s, selectionEnd: e } = el;

	// Find the start of the first selected line
	const lineStart = value.lastIndexOf('\n', s - 1) + 1;
	// Find the end of the last selected line
	const lineEnd = value.indexOf('\n', e);
	const actualEnd = lineEnd === -1 ? value.length : lineEnd;

	const block = value.slice(lineStart, actualEnd);
	const prefixed = block
		.split('\n')
		.map((line) => prefix + line)
		.join('\n');

	const lineCount = block.split('\n').length;

	return {
		value: value.slice(0, lineStart) + prefixed + value.slice(actualEnd),
		selectionStart: s + prefix.length,
		selectionEnd: e + prefix.length * lineCount,
	};
}

/**
 * Insert a block of text at cursor position, ensuring blank lines around it.
 * @param {HTMLTextAreaElement} el
 * @param {string} block
 * @param {number} [cursorOffset] — offset from start of inserted block for cursor placement
 * @returns {{ value: string, selectionStart: number, selectionEnd: number }}
 */
export function insertBlock(el, block, cursorOffset) {
	const { value, selectionStart: s } = el;

	// Ensure blank line before if not at start
	let pre = '';
	if (s > 0 && value[s - 1] !== '\n') pre = '\n';
	if (s > 1 && value[s - 2] !== '\n') pre = '\n\n';

	const inserted = pre + block + '\n';
	const cursorPos = cursorOffset != null
		? s + pre.length + cursorOffset
		: s + inserted.length;

	return {
		value: value.slice(0, s) + inserted + value.slice(s),
		selectionStart: cursorPos,
		selectionEnd: cursorPos,
	};
}

/**
 * Apply an insertion result to a textarea and update the bound value.
 * @param {HTMLTextAreaElement} el
 * @param {{ value: string, selectionStart: number, selectionEnd: number }} result
 * @param {(v: string) => void} setValue — callback to update the reactive binding
 */
export function applyResult(el, result, setValue) {
	setValue(result.value);
	// Need to wait for Svelte to update the DOM, then set selection
	requestAnimationFrame(() => {
		el.selectionStart = result.selectionStart;
		el.selectionEnd = result.selectionEnd;
		el.focus();
	});
}
