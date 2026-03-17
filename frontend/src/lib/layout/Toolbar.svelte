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

	/** Map of route segment → i18n key. Covers every sidebar entry. */
	const NAV_KEYS = {
		dashboard: 'nav.dashboard',
		constitution: 'nav.constitution',
		architecture: 'nav.architecture',
		adr: 'nav.adr',
		devplan: 'nav.devplan',
		features: 'nav.features',
		tasks: 'nav.tasks',
		review: 'nav.review',
		git: 'nav.git',
		settings: 'nav.settings',
		about: 'nav.about',
	};

	let projectName = $derived($status?.project_name || '');

	let currentTab = $derived.by(() => {
		const parts = $page.url.pathname.split('/').filter(Boolean);
		return parts[0] || 'dashboard';
	});

	/**
	 * Build breadcrumb segments from the current URL.
	 * Each segment: { label, href?, isLast }
	 */
	let crumbs = $derived.by(() => {
		const parts = $page.url.pathname.split('/').filter(Boolean);
		const section = parts[0] || 'dashboard';
		const navKey = NAV_KEYS[section];
		const sectionLabel = navKey ? $t(navKey) : section;

		// Sub-page slug (e.g. tasks/[name] or features/[slug])
		const subPage = parts[1] ? decodeURIComponent(parts[1]) : null;

		const result = [];

		if (subPage) {
			// Section is a link when there's a deeper page
			result.push({ label: sectionLabel, href: `/${section}` });
			result.push({ label: subPage, href: null, isLast: true });
		} else {
			result.push({ label: sectionLabel, href: null, isLast: true });
		}

		return result;
	});
</script>

<div class="toolbar-strip">
	{#if currentTab === 'dashboard'}
	<div class="project-title">
		{projectName || 'Skaro'}
	</div>
	{:else}
	<nav class="breadcrumb" aria-label="Breadcrumb">
		<a class="crumb" href="/dashboard">{projectName || 'Skaro'}</a>
		{#each crumbs as crumb}
			<span class="sep">›</span>
			{#if crumb.href}
				<a class="crumb" href={crumb.href}>{crumb.label}</a>
			{:else}
				<span class="crumb last">{crumb.label}</span>
			{/if}
		{/each}
	</nav>
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

	a.crumb {
		color: var(--dm);
		text-decoration: none;
		transition: color 0.12s;
	}

	a.crumb:hover {
		color: var(--tx-bright);
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
