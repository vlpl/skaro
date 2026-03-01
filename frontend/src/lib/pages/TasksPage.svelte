<script>
	import { t } from '$lib/i18n/index.js';
	import { status } from '$lib/stores/statusStore.js';
	import { Package } from 'lucide-svelte';
	import TaskCard from '$lib/pages/tasks/TaskCard.svelte';

	let activeTab = $state('__all__');

	/** Sorted unique milestones extracted from tasks. */
	let milestones = $derived.by(() => {
		const tasks = $status?.tasks || [];
		const set = new Set();
		for (const task of tasks) {
			if (task.milestone) set.add(task.milestone);
		}
		return [...set].sort();
	});

	/** Tabs: one per milestone + "All" at the end. */
	let tabs = $derived.by(() => {
		return [
			{ id: '__all__', label: $t('task.all_milestones') },
			...milestones.map((ms) => ({ id: ms, label: formatMilestone(ms) })),
		];
	});

	/** Filtered tasks based on selected tab. */
	let filteredTasks = $derived.by(() => {
		const tasks = $status?.tasks || [];
		if (activeTab === '__all__') return tasks;
		return tasks.filter((t) => t.milestone === activeTab);
	});

	function formatMilestone(slug) {
		return (slug || '')
			.replace(/^\d+-/, '')
			.replace(/-/g, ' ')
			.replace(/\b\w/g, (c) => c.toUpperCase()) || slug;
	}
</script>

<div class="page-with-tabs">
	<div class="main-header">
		<h2><Package size={24} /> {$t('task.title')}</h2>
		<p>{$t('task.subtitle')}</p>
	</div>

	{#if !$status?.tasks?.length}
		<div class="card empty">
			<p>{$t('task.empty')}</p>
			<p class="hint">{$t('task.empty_hint')}</p>
		</div>
	{:else}
		<div class="milestone-tabs-layout">
			<nav class="milestone-tabs-nav">
				{#each tabs as tab}
					<button
						class="tab-item"
						class:active={activeTab === tab.id}
						onclick={() => activeTab = tab.id}
					>
						{tab.label}
					</button>
				{/each}
			</nav>
			<div class="milestone-tabs-content">
				{#each filteredTasks as task (task.name)}
					<TaskCard {task} href="/tasks/{encodeURIComponent(task.name)}" />
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.milestone-tabs-layout {
		display: flex;
		gap: 1.5rem;
		margin-top: 1.5rem;
	}

	.milestone-tabs-nav {
		position: sticky;
		top: 0;
		width: 14rem;
		flex-shrink: 0;
		align-self: flex-start;
		display: flex;
		flex-direction: column;
		gap: .2rem;
		padding: 0;
		padding-top: 1rem;
	}

	.tab-item {
		display: flex;
		align-items: center;
		width: 100%;
		padding: .75rem;
		border: none;
		border-radius: var(--r);
		background: none;
		color: var(--tx-bright);
		font-size: 1rem;
		font-family: inherit;
		text-align: left;
		cursor: pointer;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		transition: background .1s;
	}

	.tab-item:hover {
		background: var(--bg2);
	}

	.tab-item.active {
		background: var(--bg2);
		color: var(--tx-bright);
	}

	.milestone-tabs-content {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
</style>
