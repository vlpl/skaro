<script>
	import { t } from '$lib/i18n/index.js';
	import { Check, FileText, Loader2 } from 'lucide-svelte';
	import MarkdownContent from '$lib/ui/MarkdownContent.svelte';

	let { content = '', accepting = false, accepted = false, onAccept } = $props();
</script>

<h3 style="margin: 2.5rem auto 1rem auto">{$t('arch.proposed')}</h3>
<MarkdownContent content={content} />
<div class="proposed-actions">
	{#if accepted}
		<button class="btn" disabled>
			<Check size={14} />
			{$t('arch.version_accepted')}
		</button>
	{:else}
		<button class="btn btn-primary" disabled={accepting} onclick={onAccept}>
			{#if accepting}<Loader2 size={14} class="spin" />{:else}<FileText size={14} />{/if}
			{$t('arch.accept_proposed')}
		</button>
	{/if}
	<span class="hint-text">{$t('arch.accept_hint')}</span>
</div>

<style>
	.proposed-actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 1rem;
	}
	.hint-text {
		font-size: 0.75rem;
		color: var(--tx2);
	}
</style>
