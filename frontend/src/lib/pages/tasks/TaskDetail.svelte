<script>
	import { t } from '$lib/i18n/index.js';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api/client.js';
	import {
		status, taskDetail,
		lastImplementResult, lastImplementStage, lastImplementTask,
	} from '$lib/stores/statusStore.js';
	import { addLog, addError } from '$lib/stores/logStore.js';
	import { invalidate } from '$lib/api/cache.js';
	import { parseClarifications } from '$lib/utils/markdown.js';
	import MarkdownContent from '$lib/ui/MarkdownContent.svelte';
	import FileTabs from '$lib/ui/FileTabs.svelte';
	import DiffModal from '$lib/ui/DiffModal.svelte';
	import TaskHeader from './TaskHeader.svelte';
	import TaskActions from './TaskActions.svelte';
	import ClarifyForm from './ClarifyForm.svelte';
	import ImplementReview from './ImplementReview.svelte';
	import FixPanel from './FixPanel.svelte';
	import TestsPanel from './TestsPanel.svelte';

	let { taskName } = $props();

	let actionResult = $state('');
	let actionLoading = $state('');
	let activeFileTab = $state('');
	let clarifyAnswers = $state({});
	let draftSaving = $state(false);
	let draftSaved = $state(false);
	let implAppliedFiles = $state({});
	let implDiffModal = $state(null);
	let testsResults = $state(null);
	let tabInitialized = false;
	let lastQAKey = $state('');

	// Reset all local state when switching between tasks
	$effect(() => {
		// eslint-disable-next-line no-unused-expressions
		taskName; // track dependency
		actionResult = '';
		actionLoading = '';
		activeFileTab = '';
		clarifyAnswers = {};
		draftSaving = false;
		draftSaved = false;
		implAppliedFiles = {};
		implDiffModal = null;
		testsResults = null;
		tabInitialized = false;
		lastQAKey = '';
	});

	let detail = $derived($taskDetail);
	let freshTask = $derived($status?.tasks?.find((f) => f.name === taskName) ?? null);
	let currentStage = $derived(freshTask?.current_stage ?? detail?.state?.current_stage ?? 0);
	let totalStages = $derived(freshTask?.total_stages ?? detail?.state?.total_stages ?? 0);
	let phases = $derived(freshTask?.phases ?? detail?.state?.phases ?? {});
	let currentPhase = $derived(freshTask?.current_phase ?? detail?.state?.current_phase ?? '');
	let testsConfirmed = $derived(phases.tests === 'complete');

	// Load tests.json from detail if available (survives page reload)
	$effect(() => {
		if (detail?.name === taskName && detail?.files?.['tests.json'] && !testsResults) {
			try {
				testsResults = JSON.parse(detail.files['tests.json']);
			} catch { /* ignore parse errors */ }
		}
	});

	// ── Clarify QA ──
	let clarifyContent = $derived(detail?.files?.['clarifications.md'] || '');
	let parsedQA = $derived(clarifyContent ? parseClarifications(clarifyContent) : []);
	let hasStructuredQA = $derived(parsedQA.length > 0);
	let hasUnanswered = $derived(hasStructuredQA && parsedQA.some((q) => !q.answer.trim()));

	$effect(() => {
		const key = parsedQA.map((q) => `${q.num}:${q.answer.length}`).join(',');
		if (hasStructuredQA && key !== lastQAKey) {
			lastQAKey = key;
			const fromFile = {};
			for (const q of parsedQA) fromFile[q.num] = q.answer || '';
			clarifyAnswers = fromFile;
			draftSaved = false;
		}
	});

	// ── File tabs ──
	let fileTabs = $derived.by(() => {
		if (!detail) return [];
		const tabs = [];
		if (detail.files['spec.md']) tabs.push({ id: 'spec.md', label: $t('tab.specification') });
		if (detail.files['clarifications.md'] && !hasUnanswered) tabs.push({ id: 'clarifications.md', label: $t('tab.clarifications') });
		if (detail.files['plan.md']) tabs.push({ id: 'plan.md', label: $t('tab.plan') });
		if (detail.files['tasks.md']) tabs.push({ id: 'tasks.md', label: $t('tab.tasks') });
		Object.keys(detail.stages || {}).map(Number).sort((a, b) => a - b)
			.forEach((s) => tabs.push({ id: `stage-${s}`, label: $t('tab.stage_notes', { n: s }) }));
		if (testsResults || phases.tests === 'in_progress' || phases.tests === 'complete') {
			tabs.push({ id: 'tests', label: $t('tab.tests') });
		}
		if (currentStage > 0) tabs.push({ id: 'chat', label: $t('tab.chat') });
		return tabs;
	});

	$effect(() => {
		if (fileTabs.length > 0 && !tabInitialized) {
			tabInitialized = true;
			activeFileTab = fileTabs[0].id;
		}
	});

	let activeContent = $derived.by(() => {
		if (!detail) return '';
		const id = activeFileTab || fileTabs[fileTabs.length - 1]?.id || '';
		if (id === 'chat') return '';
		if (id === 'tests') return '';
		if (id.startsWith('stage-')) return detail.stages?.[id.replace('stage-', '')] || '';
		return detail.files?.[id] || '';
	});

	// ── Actions ──
	async function runClarify() {
		actionLoading = 'clarify'; actionResult = '';
		addLog($t('log.clarify_run', { name: taskName }));
		try {
			const result = await api.runClarify(taskName);
			if (result.success) { addLog($t('log.clarify_questions_saved')); lastQAKey = ''; await reloadAll(); }
			else handleActionError(result);
		} catch (e) { addError(e.message, 'runClarify'); actionResult = e.message; }
		actionLoading = '';
	}

	async function saveDraft() {
		if (!hasStructuredQA) return;
		draftSaving = true;
		try {
			const questions = parsedQA.map((q) => ({
				num: q.num,
				question: q.question,
				context: q.context || '',
				options: q.options || [],
				answer: clarifyAnswers[q.num] || '',
			}));
			await api.saveClarifyDraft(taskName, questions);
			draftSaved = true;
			addLog($t('log.clarify_draft_saved', { name: taskName }));
			setTimeout(() => { draftSaved = false; }, 2000);
		} catch (e) { addError(e.message, 'saveDraft'); }
		draftSaving = false;
	}

	async function submitAnswers() {
		const filled = Object.entries(clarifyAnswers).filter(([, v]) => v.trim());
		if (filled.length === 0) { addLog($t('clarify.no_answers')); return; }
		actionLoading = 'submit';
		try {
			await api.answerClarify(taskName, { questions: clarifyContent, answers: Object.fromEntries(filled) });
			addLog($t('log.clarify_done', { name: taskName }));
			clarifyAnswers = {}; lastQAKey = ''; await reloadAll();
		} catch (e) { addError(e.message, 'submitClarify'); actionResult = e.message; }
		actionLoading = '';
	}

	async function runPlan() {
		actionLoading = 'plan'; actionResult = '';
		addLog($t('log.plan_run', { name: taskName }));
		try {
			const result = await api.runPlan(taskName);
			if (result.success) { addLog($t('log.plan_done', { n: result.data?.stage_count || '?' })); await reloadAll(); }
			else handleActionError(result);
		} catch (e) { addError(e.message, 'runPlan'); actionResult = e.message; }
		actionLoading = '';
	}

	async function runImplement() {
		const stage = currentStage + 1;
		actionLoading = 'implement'; actionResult = '';
		addLog($t('log.impl_run', { name: taskName, n: stage }));
		try {
			const result = await api.runImplement(taskName, { stage });
			if (result.success) {
				implAppliedFiles = {};
				lastImplementResult.set(result);
				lastImplementStage.set(stage);
				lastImplementTask.set(taskName);
				addLog($t('log.impl_done', { n: stage, files: Object.keys(result.data?.files || {}).length }));
				await reloadAll();
				activeFileTab = `stage-${stage}`;
			} else handleActionError(result);
		} catch (e) { addError(e.message, 'runImplement'); actionResult = e.message; }
		actionLoading = '';
	}

	async function runTests() {
		actionLoading = 'tests'; actionResult = '';
		addLog($t('log.tests_run', { name: taskName }));
		try {
			const result = await api.runTests(taskName);
			if (result.success) {
				testsResults = result.data;
				addLog($t('log.tests_done', { name: taskName }));
				await reloadAll();
				activeFileTab = 'tests';
			} else handleActionError(result);
		} catch (e) { addError(e.message, 'runTests'); actionResult = e.message; }
		actionLoading = '';
	}

	async function confirmTests() {
		try {
			const result = await api.confirmTests(taskName);
			if (result.success) {
				addLog($t('log.tests_confirmed', { name: taskName }));
				await reloadAll();
			} else handleActionError(result);
		} catch (e) { addError(e.message, 'confirmTests'); }
	}

	function sendTestErrorsToLlm(errorSummary) {
		activeFileTab = 'chat';
		setTimeout(() => {
			window.dispatchEvent(new CustomEvent('skaro:prefill-fix', {
				detail: { message: errorSummary },
			}));
		}, 100);
	}

	// ── Implement file apply ──
	function openImplDiff(filepath, fileData) {
		implDiffModal = { filepath, oldContent: fileData.old, newContent: fileData.new, isNew: fileData.is_new, applied: !!implAppliedFiles[filepath] };
	}

	async function applyImplFile(filepath, content) {
		try {
			const result = await api.applyImplementFile(taskName, filepath, content);
			if (result.success) { implAppliedFiles[filepath] = true; implAppliedFiles = { ...implAppliedFiles }; addLog($t('log.fix_applied', { file: filepath })); implDiffModal = null; }
			else addError(result.message, 'applyImplFile');
		} catch (e) { addError(e.message, 'applyImplFile'); }
	}

	async function applyAllImplFiles(filesMap) {
		for (const [fpath, fdata] of Object.entries(filesMap)) {
			if (!implAppliedFiles[fpath]) await applyImplFile(fpath, fdata.new);
		}
	}

	// ── Helpers ──
	function handleActionError(result) {
		addError(result.message || $t('error.unknown'), result.error_type || '');
		actionResult = result.message || $t('error.unknown');
	}

	async function reloadAll() {
		invalidate('status', `task:${taskName}`);
		status.set(await api.getStatus());
		if (taskName) {
			taskDetail.set(await api.getTask(taskName));
		}
	}

	function goBack() {
		taskDetail.set(null);
		goto('/tasks');
	}
</script>

<div class="detail page-with-tabs">
	<TaskHeader {taskName} {phases} {currentPhase} {currentStage} {totalStages} onBack={goBack} />

	<TaskActions
		{phases} {currentStage} {totalStages} {actionLoading} {hasUnanswered}
		onClarify={runClarify} onPlan={runPlan} onImplement={runImplement} onTests={runTests}
	/>

	{#if hasUnanswered}
		<ClarifyForm
			{parsedQA} bind:clarifyAnswers {actionLoading} {draftSaving} {draftSaved}
			onSubmit={submitAnswers} onSaveDraft={saveDraft} onReClarify={runClarify}
		/>
	{/if}

	{#if $lastImplementResult && $lastImplementTask === taskName}
		<ImplementReview
			stage={$lastImplementStage}
			filesMap={$lastImplementResult.data?.files || {}}
			appliedFiles={implAppliedFiles}
			onOpenDiff={openImplDiff}
			onApplyAll={() => applyAllImplFiles($lastImplementResult.data?.files || {})}
		/>
	{/if}

	{#if implDiffModal}
		<DiffModal
			filepath={implDiffModal.filepath}
			oldContent={implDiffModal.oldContent}
			newContent={implDiffModal.newContent}
			isNew={implDiffModal.isNew}
			applied={implDiffModal.applied}
			onApply={() => applyImplFile(implDiffModal.filepath, implDiffModal.newContent)}
			onClose={() => implDiffModal = null}
		/>
	{/if}

	<FileTabs
		tabs={fileTabs}
		activeTab={activeFileTab}
		content={activeContent}
		onSelectTab={(id) => activeFileTab = id}
	>
		{#snippet chatSlot()}
			<FixPanel task={taskName} />
		{/snippet}
		{#snippet testsSlot()}
			<TestsPanel
				{taskName}
				results={testsResults}
				loading={actionLoading === 'tests'}
				confirmed={testsConfirmed}
				onRunTests={runTests}
				onConfirm={confirmTests}
				onSendToLlm={sendTestErrorsToLlm}
			/>
		{/snippet}
	</FileTabs>
</div>

<style>
	.detail { padding-bottom: 0; }
</style>
