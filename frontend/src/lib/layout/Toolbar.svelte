<script>
	import { t } from '$lib/i18n/index.js';
	import { page } from '$app/stores';
	import { status } from '$lib/stores/statusStore.js';
	import { Zap } from 'lucide-svelte';

	function formatTokens(n) {
		if (!n || n === 0) return '0';
		if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
		if (n >= 1_000) return Math.round(n / 1_000) + 'k';
		return String(n);
	}

	let projectName = $derived($status?.project_name || '');

	let currentTab = $derived.by(() => {
		const parts = $page.url.pathname.split('/').filter(Boolean);
		return parts[0] || 'dashboard';
	});

	let selectedTask = $derived.by(() => {
		const parts = $page.url.pathname.split('/').filter(Boolean);
		return parts[0] === 'tasks' && parts[1] ? decodeURIComponent(parts[1]) : null;
	});

	let selectedFeature = $derived.by(() => {
		const parts = $page.url.pathname.split('/').filter(Boolean);
		return parts[0] === 'features' && parts[1] ? decodeURIComponent(parts[1]) : null;
	});
</script>

<div class="toolbar-strip">
	{#if currentTab === 'dashboard'}
	<div class="project-title">
		{projectName || 'Skaro'}
	</div>
	{:else}
	<div class="breadcrumb">
		{#if projectName}
			<span>{projectName}</span>
		{:else}
			<span>Skaro</span>
		{/if}
		<span class="sep">›</span>
		{#if currentTab === 'constitution'}<span class="last">{$t('nav.constitution')}</span>
		{:else if currentTab === 'architecture'}<span class="last">{$t('nav.architecture')}</span>
		{:else if currentTab === 'adr'}<span class="last">{$t('nav.adr')}</span>
		{:else if currentTab === 'tasks'}
			<span class:last={!selectedTask}>{$t('nav.tasks')}</span>
			{#if selectedTask}<span class="sep">›</span><span class="last">{selectedTask}</span>{/if}
		{:else if currentTab === 'settings'}<span class="last">{$t('nav.settings')}</span>
		{:else if currentTab === 'devplan'}<span class="last">{$t('nav.devplan')}</span>
		{:else if currentTab === 'features'}
			<span class:last={!selectedFeature}>{$t('nav.features')}</span>
			{#if selectedFeature}<span class="sep">›</span><span class="last">{selectedFeature}</span>{/if}
		{/if}
	</div>
	{/if}
	<div class="tokens">
		<Zap size={11} />
		<span>Tokens: {formatTokens($status?.tokens?.total_tokens)}</span>
	</div>
</div>

<style>
	.toolbar-strip {
		height: 2.875rem;
		display: flex;
		align-items: center;
		padding: 0 1rem;
		font-size: 0.9375rem;
		color: var(--dm);
		gap: 0.25rem;
		flex-shrink: 0;
	}

	.breadcrumb {
		display: flex;
		align-items: center;
		gap: 0.375rem;
	}

	.project-title {
		font-weight: 600;
		color: var(--tx-bright);
		font-size: 1rem;
	}

	.sep {
		color: var(--dm2);
	}

	.last {
		color: var(--tx);
	}

	.tokens {
		margin-left: auto;
		display: flex;
		align-items: center;
		gap: 0.1875rem;
		color: var(--yl);
		font-family: var(--font-ui);
		font-size: 0.6875rem;
	}
</style>
