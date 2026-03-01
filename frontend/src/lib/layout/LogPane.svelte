<script>
	import { t } from '$lib/i18n/index.js';
	import { logEntries, llmActive, llmPhase, llmText } from '$lib/stores/logStore.js';

	let streamEl = $state(null);

	// Auto-scroll stream to bottom
	$effect(() => {
		if ($llmText && streamEl) {
			streamEl.scrollTop = streamEl.scrollHeight;
		}
	});
</script>

<div class="pane">
	{#if $llmActive || $llmText}
		<div class="llm-stream" class:done={!$llmActive}>
			<div class="llm-header">
				{#if $llmActive}
					<span class="llm-dot"></span>
				{/if}
				<span class="llm-label">
					{$t('panel.llm_thinking')}{$llmPhase ? ` — ${$llmPhase}` : ''}
				</span>
			</div>
			<div class="llm-body" bind:this={streamEl}>
				<pre>{$llmText || '…'}</pre>
			</div>
		</div>
	{/if}

	<div class="log-list">
		{#if $logEntries.length === 0 && !$llmActive && !$llmText}
			<div class="empty">{$t('panel.no_activity')}</div>
		{:else}
			{#each $logEntries as entry}
				<div class="log-entry">
					<span class="log-time">{entry.time}</span>
					<span class="log-text">{entry.text}</span>
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.pane {
		height: 100%;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.empty {
		padding: 0.75rem;
		color: var(--dm);
	}

	/* ── LLM Stream — fills all available space ── */

	.llm-stream {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		border-bottom: 0.0625rem solid var(--ac);
		background: color-mix(in srgb, var(--ac) 5%, transparent);
		transition: opacity 0.3s;
	}

	.llm-stream.done {
		opacity: 0.5;
	}

	.llm-header {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.25rem 0.75rem 0.125rem;
		font-size: 0.6875rem;
		font-weight: 600;
		color: var(--ac);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		flex-shrink: 0;
	}

	.llm-dot {
		width: 0.375rem;
		height: 0.375rem;
		border-radius: 50%;
		background: var(--ac);
		animation: pulse 1s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.llm-body {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		padding: 0 0.75rem 0.375rem;
	}

	.llm-body pre {
		margin: 0;
		font-family: var(--font-ui);
		font-size: 0.75rem;
		line-height: 1.5;
		color: var(--dm);
		white-space: pre-wrap;
		word-break: break-word;
	}

	/* ── Log entries — shrinks to min 1 row when LLM active ── */

	.log-list {
		flex-shrink: 0;
		max-height: 100%;
		overflow-y: auto;
	}

	/* When LLM stream is visible, show at most ~1 row */
	.llm-stream ~ .log-list {
		max-height: 1.5rem;
		overflow: hidden;
	}

	.log-entry {
		padding: 0.125rem 0.75rem;
		display: flex;
		gap: 0.625rem;
		line-height: 1.25rem;
		border-bottom: 0.0625rem solid var(--bd);
	}

	.log-entry:hover {
		background: var(--sf-hover);
	}

	.log-time {
		color: var(--dm2);
		flex-shrink: 0;
		font-variant-numeric: tabular-nums;
		min-width: 4.375rem;
	}

	.log-text {
		color: var(--tx);
	}
</style>
