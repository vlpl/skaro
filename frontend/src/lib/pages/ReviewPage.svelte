<script>
	import { onMount } from 'svelte';
	import { t } from '$lib/i18n/index.js';
	import { api } from '$lib/api/client.js';
	import { status } from '$lib/stores/statusStore.js';
	import { addLog, addError } from '$lib/stores/logStore.js';
	import { invalidate } from '$lib/api/cache.js';
	import { ShieldCheck } from 'lucide-svelte';
	import FileTabs from '$lib/ui/FileTabs.svelte';
	import ProjectTestsPanel from './review/ProjectTestsPanel.svelte';
	import ProjectFixPanel from './review/ProjectFixPanel.svelte';

	let activeTab = $state('tests');
	let testsResults = $state(null);
	let testsLoading = $state(false);

	onMount(() => { loadResults(); });

	async function loadResults() {
		try {
			const data = await api.getReviewResults();
			if (data.results) testsResults = data.results;
		} catch { /* no previous results */ }
	}

	async function runTests() {
		testsLoading = true;
		addLog($t('review.running_tests'));
		try {
			const result = await api.runReviewTests();
			if (result.success) {
				testsResults = result.data;
				addLog($t('review.tests_done'));
				invalidate('status');
				status.set(await api.getStatus());
			} else {
				addError(result.message || 'Review tests failed', 'reviewTests');
			}
		} catch (e) {
			addError(e.message, 'runReviewTests');
		}
		testsLoading = false;
	}

	function sendErrorsToFix(errorSummary) {
		activeTab = 'chat';
		setTimeout(() => {
			window.dispatchEvent(new CustomEvent('skaro:prefill-project-fix', {
				detail: { message: errorSummary },
			}));
		}, 100);
	}

	let reviewTabs = $derived([
		{ id: 'tests', label: $t('review.tab_tests') },
		{ id: 'chat', label: $t('review.tab_fix') },
	]);
</script>

<div class="page-with-tabs">
	<div class="main-header">
		<h2><ShieldCheck size={24} /> {$t('review.title')}</h2>
		<p>{$t('review.subtitle')}</p>
	</div>

	<FileTabs
		tabs={reviewTabs}
		activeTab={activeTab}
		content=""
		onSelectTab={(id) => activeTab = id}
	>
		{#snippet testsSlot()}
			<ProjectTestsPanel
				results={testsResults}
				loading={testsLoading}
				onRunTests={runTests}
				onSendToFix={sendErrorsToFix}
			/>
		{/snippet}
		{#snippet chatSlot()}
			<ProjectFixPanel />
		{/snippet}
	</FileTabs>
</div>
