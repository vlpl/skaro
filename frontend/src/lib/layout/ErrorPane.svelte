<script>
	import { t } from '$lib/i18n/index.js';
	import { errorEntries } from '$lib/stores/logStore.js';
</script>

<div class="pane">
	{#if $errorEntries.length === 0}
		<div class="empty">{$t('panel.no_problems')}</div>
	{:else}
		{#each $errorEntries as entry}
			<div class="error-entry">
				<span class="err-time">{entry.time}</span>
				<span class="err-text">
					{entry.text}
					{#if entry.context}<span class="err-ctx">{entry.context}</span>{/if}
				</span>
			</div>
		{/each}
	{/if}
</div>

<style>
	.pane {
		height: 100%;
		overflow-y: auto;
	}

	.empty {
		padding: 0.75rem;
		color: var(--dm);
	}

	.error-entry {
		padding: 0.25rem 0.75rem;
		display: flex;
		gap: 0.625rem;
		line-height: 1.25rem;
		border-bottom: 0.0625rem solid var(--bd);
	}

	.error-entry:hover {
		background: rgba(244, 71, 71, .06);
	}

	.err-time {
		color: var(--dm2);
		flex-shrink: 0;
		font-variant-numeric: tabular-nums;
		min-width: 4.375rem;
	}

	.err-text {
		color: var(--rd);
	}

	.err-ctx {
		color: var(--dm);
		margin-left: 0.5rem;
	}
</style>
