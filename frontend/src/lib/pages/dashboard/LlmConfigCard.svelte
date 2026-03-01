<script>
	import { t } from '$lib/i18n/index.js';
	import { Cpu } from 'lucide-svelte';

	let { config = {}, roles = [] } = $props();
</script>

<div class="widget lg card">
	<div class="section-head">
		<h3><Cpu size={16} /> {$t('dash.llm_config')}</h3>
		<a class="sec-btn" href="/settings">{$t('dash.edit')}</a>
	</div>
	<div class="llm-grid">
		<div class="llm-item default">
			<span class="llm-label">{$t('dash.default_model')}</span>
			<span class="llm-val">{config?.llm_provider || '—'} / {config?.llm_model || '—'}</span>
		</div>
		{#each roles as role}
			<div class="llm-item">
				<span class="llm-label">{$t('settings.role_' + role.name)}</span>
				<span class="llm-val">{role.provider} / {role.model}</span>
			</div>
		{/each}
		{#if roles.length === 0}
			<div class="llm-item hint">
				<span class="llm-label">{$t('dash.no_roles')}</span>
			</div>
		{/if}
	</div>
</div>

<style>
	/* .section-head, .sec-btn → app.css */

	.llm-grid {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.llm-item {
		background: var(--bg2);
		border: none;
		border-radius: var(--r2);
		padding: 0.5rem 0.875rem;
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}

	.llm-label {
		font-size: 0.625rem;
		text-transform: uppercase;
		letter-spacing: 0.03rem;
		color: var(--dm);
	}

	.llm-val {
		font-size: 0.8125rem;
		color: var(--tx-bright);
		font-family: var(--font-ui);
	}

	.llm-item.hint .llm-label { color: var(--dm2); font-style: italic; text-transform: none; }
</style>
