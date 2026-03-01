<script>
	import { t } from '$lib/i18n/index.js';
	import { Check, X, Loader2 } from 'lucide-svelte';
	import MarkdownContent from '$lib/ui/MarkdownContent.svelte';
	import PlanTaskCard from './PlanTaskCard.svelte';

	let {
		mode = 'initial',
		items = [],
		proposedDevplan = '',
		rawResponse = '',
		confirming = false,
		onConfirm = () => {},
		onDiscard = () => {},
	} = $props();

	let isUpdate = $derived(mode === 'update');
</script>

{#if isUpdate}
	<div class="card" style="margin-top: 2rem">
		<h3 class="section-title">{$t('devplan.update_proposed')}</h3>
		<p class="subtitle">{$t('devplan.update_review')}</p>

		{#if proposedDevplan}
			<details class="proposal-details" open>
				<summary class="details-summary">{$t('devplan.updated_plan')}</summary>
				<MarkdownContent content={proposedDevplan} />
			</details>
		{/if}

		{#if items.length > 0}
			<details class="proposal-details" open>
				<summary class="details-summary">{$t('devplan.new_tasks', { n: items.length })}</summary>
				{#each items as f, i}
					<PlanTaskCard task={f} index={i} />
				{/each}
			</details>
		{/if}

		{#if !proposedDevplan && rawResponse}
			<details class="proposal-details" open>
				<summary class="details-summary">{$t('devplan.llm_response')}</summary>
				<MarkdownContent content={rawResponse} />
			</details>
		{/if}

		<div class="btn-group">
			<button class="btn btn-success" disabled={confirming} onclick={onConfirm}>
				{#if confirming}<Loader2 size={14} class="spin" />{/if}
				<Check size={14} /> {$t('devplan.confirm_update')}
			</button>
			<button class="btn btn-danger" onclick={onDiscard}>
				<X size={14} /> {$t('devplan.discard_update')}
			</button>
		</div>
	</div>
{:else}
	<h3 class="section-title">{$t('devplan.proposed')}</h3>
	<p class="subtitle">{$t('devplan.review_text')}</p>
	{#each items as f, i}
		<PlanTaskCard task={f} index={i} />
	{/each}
	<div class="btn-group">
		<button class="btn btn-success" disabled={confirming} onclick={onConfirm}>
			<Check size={14} /> {$t('devplan.confirm')}
		</button>
		<button class="btn btn-danger" onclick={onDiscard}>
			<X size={14} /> {$t('devplan.discard')}
		</button>
	</div>
{/if}

<style>
	.section-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--tx-bright);
		margin-bottom: 0.5rem;
	}

	.proposal-details {
		margin: 0.625rem 0;
	}

	.details-summary {
		cursor: pointer;
		color: var(--ac);
		font-size: 0.8125rem;
		font-weight: 600;
		margin-bottom: 0.375rem;
	}
</style>
