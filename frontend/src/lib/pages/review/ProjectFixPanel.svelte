<script>
	import { t } from '$lib/i18n/index.js';
	import { onMount, onDestroy } from 'svelte';
	import { api } from '$lib/api/client.js';
	import { status } from '$lib/stores/statusStore.js';
	import { addLog, addError } from '$lib/stores/logStore.js';
	import { Loader2, ChevronDown, ChevronRight } from 'lucide-svelte';
	import ChatMessage from '$lib/pages/tasks/ChatMessage.svelte';
	import ComposeBox from '$lib/pages/tasks/ComposeBox.svelte';
	import DiffModal from '$lib/ui/DiffModal.svelte';

	let message = $state('');
	let loading = $state(false);
	let conversationLoading = $state(false);
	let conversation = $state([]);
	let contextTokens = $state(0);
	let initialLoaded = $state(false);
	let appliedFiles = $state({});
	let diffModal = $state(null);
	let abortController = $state(null);

	// Scope selection
	let scopeData = $state(null);
	let selectedTasks = $state([]);
	let scopeExpanded = $state(false);

	let allTaskNames = $derived(
		scopeData?.milestones?.flatMap((ms) => ms.tasks) || []
	);
	let allSelected = $derived(
		allTaskNames.length > 0 && selectedTasks.length === allTaskNames.length
	);

	let modelDisplay = $derived.by(() => {
		const s = $status;
		if (!s?.config) return '';
		const cfg = s.config;
		if (cfg.roles?.reviewer) return `${cfg.roles.reviewer.provider} / ${cfg.roles.reviewer.model}`;
		return `${cfg.llm_provider} / ${cfg.llm_model}`;
	});

	onMount(() => {
		loadConversation();
		loadScope();
	});

	function handlePrefill(e) {
		const text = e.detail?.message;
		if (text) {
			message = text;
			scrollToEnd('smooth');
		}
	}

	onMount(() => { window.addEventListener('skaro:prefill-project-fix', handlePrefill); });
	onDestroy(() => { window.removeEventListener('skaro:prefill-project-fix', handlePrefill); });

	$effect(() => {
		void conversation.length;
		void loading;
		scrollToEnd('smooth');
	});

	function scrollToEnd(behavior = 'instant') {
		requestAnimationFrame(() => {
			const main = document.querySelector('.main');
			if (main) main.scrollTo({ top: main.scrollHeight, behavior });
		});
	}

	async function loadConversation() {
		conversationLoading = true;
		try {
			const data = await api.loadProjectFixConversation();
			if (data.conversation?.length > 0) conversation = data.conversation;
			contextTokens = data.context_tokens || 0;
		} catch { /* empty is fine */ }
		conversationLoading = false;
		initialLoaded = true;
	}

	async function loadScope() {
		try {
			scopeData = await api.getReviewScope();
			// Select all tasks by default
			if (scopeData?.milestones) {
				selectedTasks = scopeData.milestones.flatMap((ms) => ms.tasks);
			}
		} catch { /* ignore */ }
	}

	let conversationTokens = $derived(
		Math.round(conversation.reduce((sum, t) => sum + (t.content?.length || 0), 0) / 4)
	);
	let messageTokens = $derived(Math.round(message.length / 4));
	let totalTokens = $derived(contextTokens + conversationTokens + messageTokens);
	let tokenDisplay = $derived.by(() => {
		const k = totalTokens / 1000;
		return k >= 1 ? `~${k.toFixed(0)}k ${$t('fix.tokens')}` : `~${totalTokens} ${$t('fix.tokens')}`;
	});

	function toggleTask(taskName) {
		if (selectedTasks.includes(taskName)) {
			selectedTasks = selectedTasks.filter((t) => t !== taskName);
		} else {
			selectedTasks = [...selectedTasks, taskName];
		}
	}

	function toggleMilestone(tasks) {
		const allSelected = tasks.every((t) => selectedTasks.includes(t));
		if (allSelected) {
			selectedTasks = selectedTasks.filter((t) => !tasks.includes(t));
		} else {
			const toAdd = tasks.filter((t) => !selectedTasks.includes(t));
			selectedTasks = [...selectedTasks, ...toAdd];
		}
	}

	async function sendMessage() {
		const text = message.trim();
		if (!text || loading) return;
		loading = true;
		message = '';
		conversation = [...conversation, { role: 'user', content: text }];

		const controller = new AbortController();
		abortController = controller;

		try {
			const history = conversation.slice(0, -1).map((turn) => ({ role: turn.role, content: turn.content }));
			const result = await api.sendProjectFix(text, history, allSelected ? [] : selectedTasks, controller.signal);
			if (result.success) {
				conversation = [...conversation, {
					role: 'assistant', content: result.message,
					files: result.files || {}, turnIndex: conversation.length,
				}];
				addLog($t('review.fix_response'));
			} else {
				addError(result.message || 'Project fix failed', 'projectFix');
			}
		} catch (e) {
			if (e.name === 'AbortError') {
				addLog($t('fix.cancelled'));
			} else {
				addError(e.message, 'sendProjectFix');
			}
		}
		abortController = null;
		loading = false;
	}

	function cancelRequest() {
		if (abortController) abortController.abort();
	}

	async function applyFile(turnIndex, filepath, content) {
		try {
			const result = await api.applyProjectFixFile(filepath, content);
			if (result.success) {
				if (!appliedFiles[turnIndex]) appliedFiles[turnIndex] = {};
				appliedFiles[turnIndex][filepath] = true;
				appliedFiles = { ...appliedFiles };
				addLog($t('log.fix_applied', { file: filepath }));
				diffModal = null;
			} else { addError(result.message, 'applyProjectFix'); }
		} catch (e) { addError(e.message, 'applyProjectFix'); }
	}

	function openDiff(turnIndex, filepath, fileData) {
		diffModal = {
			filepath, oldContent: fileData.old, newContent: fileData.new,
			isNew: fileData.is_new, applied: !!(appliedFiles[turnIndex]?.[filepath]),
			turnIndex,
		};
	}

	async function clearConversation() {
		conversation = []; appliedFiles = {}; message = '';
		try { await api.clearProjectFixConversation(); } catch {}
	}
</script>

<div class="project-fix">
	<!-- Scope selector -->
	{#if scopeData && scopeData.milestones?.length > 0}
		<div class="scope-section">
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="scope-header" onclick={() => scopeExpanded = !scopeExpanded}>
				{#if scopeExpanded}<ChevronDown size={14} />{:else}<ChevronRight size={14} />{/if}
				<span class="scope-title">{$t('review.scope_title')}</span>
				<span class="scope-hint">
					{allSelected
						? $t('review.scope_all')
						: $t('review.scope_selected', { n: selectedTasks.length })}
				</span>
			</div>
			{#if scopeExpanded}
				<div class="scope-body">
					{#each scopeData.milestones as ms}
						<div class="scope-milestone">
							<label class="scope-ms-label">
								<input
									type="checkbox"
									checked={ms.tasks.every((t) => selectedTasks.includes(t))}
									indeterminate={ms.tasks.some((t) => selectedTasks.includes(t)) && !ms.tasks.every((t) => selectedTasks.includes(t))}
									onchange={() => toggleMilestone(ms.tasks)}
								/>
								<strong>{ms.slug}</strong>
							</label>
							<div class="scope-tasks">
								{#each ms.tasks as taskName}
									<label class="scope-task-label">
										<input
											type="checkbox"
											checked={selectedTasks.includes(taskName)}
											onchange={() => toggleTask(taskName)}
										/>
										{taskName}
									</label>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	<!-- Conversation -->
	{#if conversationLoading}
		<div class="fix-conversation">
			<div class="turn turn-assistant skel-turn">
				<div class="skel-label skel-pulse" style="width: 8rem"></div>
				<div class="skel-body-assistant">
					<div class="skel-line skel-pulse" style="width: 100%"></div>
					<div class="skel-line skel-pulse" style="width: 80%"></div>
					<div class="skel-line skel-pulse" style="width: 60%"></div>
				</div>
			</div>
		</div>
	{:else if conversation.length > 0}
		<div class="fix-conversation">
			{#each conversation as turn, i}
				<ChatMessage {turn} index={i} {appliedFiles} {modelDisplay} onOpenDiff={openDiff} />
			{/each}
			{#if loading}
				<div class="turn turn-assistant">
					<div class="turn-label">{modelDisplay || $t('fix.llm')}</div>
					<div class="thinking"><Loader2 size={14} class="spin" /> {$t('fix.thinking')}</div>
				</div>
			{/if}
		</div>
	{/if}

	{#if conversation.length > 0}
		<div class="clear-row">
			<button class="btn btn-sm" onclick={clearConversation}>{$t('fix.clear')}</button>
		</div>
	{/if}

	{#if diffModal}
		<DiffModal
			filepath={diffModal.filepath}
			oldContent={diffModal.oldContent}
			newContent={diffModal.newContent}
			isNew={diffModal.isNew}
			applied={diffModal.applied}
			onApply={() => applyFile(diffModal.turnIndex, diffModal.filepath, diffModal.newContent)}
			onClose={() => diffModal = null}
		/>
	{/if}

	<div class="fix-bar">
		<ComposeBox bind:message {loading} {tokenDisplay} {modelDisplay} onSend={sendMessage} onCancel={cancelRequest} />
	</div>
</div>

<style>
	.project-fix { padding-bottom: 0; }

	.scope-section {
		margin-bottom: 1rem;
		border: 1px solid var(--bd);
		border-radius: var(--r);
		overflow: hidden;
	}

	.scope-header {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		cursor: pointer; font-size: 0.8125rem; color: var(--tx);
		transition: background 0.1s;
	}
	.scope-header:hover { background: var(--bg2); }

	.scope-title { font-weight: 600; }

	.scope-hint {
		margin-left: auto; font-size: 0.75rem;
		color: var(--dm); font-family: var(--font-ui);
	}

	.scope-body {
		padding: 0.5rem 0.75rem;
		border-top: 1px solid var(--bd);
		display: flex; flex-direction: column; gap: 0.5rem;
	}

	.scope-milestone { display: flex; flex-direction: column; gap: 0.25rem; }

	.scope-ms-label {
		display: flex; align-items: center; gap: 0.375rem;
		font-size: 0.8125rem; color: var(--tx); cursor: pointer;
	}

	.scope-ms-label input,
	.scope-task-label input {
		accent-color: var(--ac);
		cursor: pointer;
	}

	.scope-tasks {
		padding-left: 1.25rem;
		display: flex; flex-direction: column; gap: 0.125rem;
	}

	.scope-task-label {
		display: flex; align-items: center; gap: 0.375rem;
		font-size: 0.8125rem; color: var(--dm); cursor: pointer;
	}
	.scope-task-label:hover { color: var(--tx); }

	.fix-conversation { padding-bottom: 1rem; }

	.fix-bar {
		position: sticky; bottom: 0;
		background: linear-gradient(0deg, rgba(38, 38, 38, 1) 0%, rgba(38, 38, 38, 1) 77%, rgba(38, 38, 38, 0) 100%);
		padding: 0; z-index: 10;
	}

	.thinking {
		display: flex; align-items: center; gap: 0.375rem;
		color: var(--dm); font-size: 0.8125rem;
	}

	.turn-label {
		font-size: 0.6875rem; font-weight: 700;
		text-transform: uppercase; letter-spacing: .05em;
		margin-bottom: 0.25rem; color: var(--or);
	}

	.clear-row {
		display: flex; justify-content: center;
		padding: 0.5rem 0;
	}

	.btn-sm { font-size: 0.75rem; padding: 0.25rem 0.625rem; }

	/* Skeleton */
	.skel-turn { pointer-events: none; }
	.skel-pulse {
		background: var(--bg2); border-radius: var(--r);
		animation: skel-shimmer 1.5s ease-in-out infinite;
	}
	@keyframes skel-shimmer { 0%, 100% { opacity: .4; } 50% { opacity: .15; } }
	.skel-label { height: .75rem; margin-bottom: .5rem; border-radius: .25rem; }
	.skel-line { height: .85rem; margin-bottom: .5rem; border-radius: .25rem; }
	.skel-body-assistant { padding: .25rem 0; }
</style>
