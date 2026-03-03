<script>
	import { t } from '$lib/i18n/index.js';
	import { status } from '$lib/stores/statusStore.js';
	import { Package } from 'lucide-svelte';
	import TaskCard from '$lib/pages/tasks/TaskCard.svelte';

	let activeTab = $state('__all__');
	let statusFilter = $state('all'); // 'all' | 'active' | 'done'

	/** Returns true when all relevant phases of a task are complete. */
	function isTaskDone(task) {
		const phases = task.phases;
		if (!phases || Object.keys(phases).length === 0) return false;
		return ['clarify', 'plan', 'implement', 'tests'].every(
			(k) => phases[k] === 'complete'
		);
	}

	/** Apply status filter to a task list. */
	function applyStatusFilter(tasks) {
		if (statusFilter === 'done') return tasks.filter(isTaskDone);
		if (statusFilter === 'active') return tasks.filter((t) => !isTaskDone(t));
		return tasks;
	}

	/** Sorted unique milestones extracted from all tasks. */
	let milestones = $derived.by(() => {
		const tasks = $status?.tasks || [];
		const set = new Set();
		for (const task of tasks) {
			if (task.milestone) set.add(task.milestone);
		}
		return [...set].sort();
	});

	/** Tasks for a given tab (milestone filter only). */
	function tasksForTab(tabId) {
		const tasks = $status?.tasks || [];
		return tabId === '__all__' ? tasks : tasks.filter((t) => t.milestone === tabId);
	}

	/** Tabs: "All" + one per milestone. */
	let tabs = $derived.by(() => [
		{ id: '__all__', label: $t('task.all_milestones') },
		...milestones.map((ms) => ({ id: ms, label: formatMilestone(ms) })),
	]);

	/** Tasks visible in the content area - both filters applied. */
	let filteredTasks = $derived.by(() =>
		applyStatusFilter(tasksForTab(activeTab))
	);

	function formatMilestone(slug) {
		return (slug || '')
			.replace(/^\d+-/, '')
			.replace(/-/g, ' ')
			.replace(/\b\w/g, (c) => c.toUpperCase()) || slug;
	}

	/** Badge count for a tab - respects the active status filter. */
	function tabCount(tabId) {
		return applyStatusFilter(tasksForTab(tabId)).length;
	}
</script>

<div class="page-with-tabs">
	<div class="main-header">
		<div class="header-left">
			<h2><Package size={24} /> {$t('task.title')}</h2>
			<p>{$t('task.subtitle')}</p>
		</div>
		{#if $status?.tasks?.length}
			<div class="status-filters">
				<button
					class="filter-btn"
					class:active={statusFilter === 'all'}
					onclick={() => statusFilter = 'all'}
				>{$t('task.filter_all')}</button>
				<button
					class="filter-btn"
					class:active={statusFilter === 'active'}
					onclick={() => statusFilter = 'active'}
				>{$t('task.filter_active')}</button>
				<button
					class="filter-btn"
					class:active={statusFilter === 'done'}
					onclick={() => statusFilter = 'done'}
				>{$t('task.filter_done')}</button>
			</div>
		{/if}
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
					{@const count = tabCount(tab.id)}
					<button
						class="tab-item"
						class:active={activeTab === tab.id}
						onclick={() => activeTab = tab.id}
					>
						<span class="tab-label">{tab.label}</span>
						<span class="tab-badge" class:tab-badge-active={activeTab === tab.id}>{count}</span>
					</button>
				{/each}
			</nav>
			<div class="milestone-tabs-content">
				{#each filteredTasks as task (task.name)}
					<TaskCard {task} href="/tasks/{encodeURIComponent(task.name)}" />
				{/each}
				{#if filteredTasks.length === 0}
					<div class="card empty">
						<p class="hint">{$t('task.filter_empty_' + statusFilter)}</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.main-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.header-left {
		min-width: 0;
	}

	/* Status filter buttons */
	.status-filters {
		display: flex;
		gap: 0.25rem;
		align-items: center;
		flex-shrink: 0;
		padding-top: 0.25rem;
	}

	.filter-btn {
		padding: 0.3125rem 0.75rem;
		border: 0.0625rem solid var(--bd);
		border-radius: var(--r);
		background: none;
		color: var(--dm);
		font-size: 0.8125rem;
		font-family: inherit;
		cursor: pointer;
		transition: background .1s, color .1s, border-color .1s;
		white-space: nowrap;
	}

	.filter-btn:hover {
		background: var(--bg2);
		color: var(--tx-bright);
	}

	.filter-btn.active {
		background: var(--bg2);
		color: var(--tx-bright);
		border-color: var(--ac);
	}

	/* Layout */
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

	/* Tab items */
	.tab-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
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
		transition: background .1s;
	}

	.tab-item:hover {
		background: var(--bg2);
	}

	.tab-item.active {
		background: var(--bg2);
		color: var(--tx-bright);
	}

	.tab-label {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/* Tab badge */
	.tab-badge {
		flex-shrink: 0;
		min-width: 1.25rem;
		padding: 0 0.375rem;
		border-radius: 0.5rem;
		background: var(--sf);
		color: var(--dm);
		font-size: 0.75rem;
		font-family: var(--font-ui);
		line-height: 1.25rem;
		text-align: center;
		transition: background .1s, color .1s;
	}

	.tab-badge-active {
		background: color-mix(in srgb, var(--ac) 15%, transparent);
		color: var(--ac);
	}

	/* Content area */
	.milestone-tabs-content {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
</style>
