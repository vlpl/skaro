<script>
	import { untrack } from 'svelte';
	import { wrapSelection, prefixLine, insertBlock, applyResult } from './insertTag.js';
	import EditorToolbar from './EditorToolbar.svelte';
	import PreviewPane from './PreviewPane.svelte';
	import EditorPane from './EditorPane.svelte';
	import SplitDivider from './SplitDivider.svelte';

	/**
	 * @type {{
	 *   content: string,
	 *   onSave: (text: string) => void | Promise<void>,
	 *   onClose: () => void,
	 * }}
	 */
	let { content, onSave, onClose } = $props();

	// Initialize once from prop without re-tracking
	let editText = $state(untrack(() => content || ''));
	let saving = $state(false);
	let splitRatio = $state(0.5);

	/** @type {HTMLTextAreaElement | null} */
	let textareaEl = $state(null);

	// ── Keyboard shortcuts ──
	function handleKeydown(e) {
		if (e.key === 'Escape') {
			onClose();
			return;
		}
		if ((e.ctrlKey || e.metaKey) && e.key === 's') {
			e.preventDefault();
			save();
		}
	}

	// ── Toolbar actions ──
	const actionMap = {
		h1:        () => prefixLine(textareaEl, '# '),
		h2:        () => prefixLine(textareaEl, '## '),
		h3:        () => prefixLine(textareaEl, '### '),
		bold:      () => wrapSelection(textareaEl, '**', '**', 'bold'),
		italic:    () => wrapSelection(textareaEl, '*', '*', 'italic'),
		code:      () => wrapSelection(textareaEl, '`', '`', 'code'),
		hr:        () => insertBlock(textareaEl, '---'),
		ul:        () => prefixLine(textareaEl, '- '),
		ol:        () => prefixLine(textareaEl, '1. '),
		quote:     () => prefixLine(textareaEl, '> '),
		checkbox:  () => prefixLine(textareaEl, '- [ ] '),
		link:      () => wrapSelection(textareaEl, '[', '](url)', 'link text'),
		codeblock: () => insertBlock(textareaEl, '```\n\n```', 4),
	};

	function handleAction(action) {
		if (!textareaEl) return;
		const fn = actionMap[action];
		if (!fn) return;
		const result = fn();
		applyResult(textareaEl, result, (v) => { editText = v; });
	}

	// ── Save ──
	async function save() {
		saving = true;
		try {
			await onSave(editText);
		} finally {
			saving = false;
		}
	}

	function handleResize(ratio) {
		splitRatio = ratio;
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="md-editor-overlay" role="dialog" aria-modal="true" aria-label="Markdown Editor">
	<div class="md-editor-modal">
		<EditorToolbar {onClose} onSave={save} onAction={handleAction} {saving} {splitRatio} />

		<div class="split-container">
			<div class="split-left" style="flex-basis: {splitRatio * 100}%;">
				<PreviewPane content={editText} />
			</div>

			<SplitDivider onResize={handleResize} />

			<div class="split-right" style="flex-basis: {(1 - splitRatio) * 100}%;">
				<EditorPane bind:value={editText} bind:textareaEl />
			</div>
		</div>
	</div>
</div>

<style>
	.md-editor-overlay {
		position: fixed;
		inset: 0;
		z-index: 1100;
		background: var(--bg);
		display: flex;
		flex-direction: column;
		/* Break out of .main > * max-width constraint */
		max-width: none !important;
		margin: 0 !important;
		width: 100vw !important;
	}

	.md-editor-modal {
		display: flex;
		flex-direction: column;
		width: 100%;
		height: 100%;
		overflow: hidden;
	}

	.split-container {
		flex: 1;
		display: flex;
		min-height: 0;
		overflow: hidden;
	}

	.split-left,
	.split-right {
		min-width: 0;
		overflow: hidden;
	}
</style>
