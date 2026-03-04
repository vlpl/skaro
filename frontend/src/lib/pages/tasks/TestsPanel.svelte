<script>
	import { t } from '$lib/i18n/index.js';
	import { api } from '$lib/api/client.js';
	import { addLog, addError } from '$lib/stores/logStore.js';
	import {
		Send, RotateCcw, Check, Loader2, Pencil, Plus, Trash2, Save,
	} from 'lucide-svelte';
	import CheckList from '$lib/ui/CheckList.svelte';
	import CommandList from '$lib/ui/CommandList.svelte';
	import TestsSummary from '$lib/ui/TestsSummary.svelte';
	import { buildErrorSummary } from '$lib/ui/testUtils.js';

	let {
		taskName = '',
		results = null,
		loading = false,
		confirmed = false,
		onRunTests = () => {},
		onConfirm = () => {},
		onSendToLlm = () => {},
	} = $props();

	let editingTaskCmds = $state(false);
	let editableCmds = $state([]);
	let savingCmds = $state(false);

	let hasErrors = $derived(results && !results.passed);
	let hasResults = $derived(results !== null);

	// ── Inline editing ──

	async function startEditingTaskCmds() {
		try {
			const data = await api.getVerifyCommands(taskName);
			editableCmds = (data.commands || []).map((c) => ({ ...c }));
		} catch {
			editableCmds = (results?.task_commands || []).map((c) => ({
				name: c.name,
				command: c.command,
			}));
		}
		editingTaskCmds = true;
	}

	function addCmd() {
		editableCmds = [...editableCmds, { name: '', command: '' }];
	}

	function removeCmd(i) {
		editableCmds = editableCmds.filter((_, idx) => idx !== i);
	}

	async function saveTaskCmds() {
		const valid = editableCmds.filter((c) => c.command.trim());
		savingCmds = true;
		try {
			await api.saveVerifyCommands(taskName, valid);
			addLog($t('tests.commands_saved'));
			editingTaskCmds = false;
		} catch (e) {
			addError(e.message, 'saveVerifyCommands');
		}
		savingCmds = false;
	}

	function cancelEditCmds() {
		editingTaskCmds = false;
		editableCmds = [];
	}

	function handleSendToLlm() {
		onSendToLlm(buildErrorSummary(results?.checklist, results?.task_commands));
	}
</script>

<div class="tests-panel">
	{#if hasResults}
		<!-- Checklist -->
		<div class="tests-section">
			<h4 class="section-title">{$t('tests.checklist_title')}</h4>
			<CheckList checks={results.checklist} />
		</div>

		<!-- Task commands -->
		<div class="tests-section">
			<div class="section-header">
				<h4 class="section-title">{$t('tests.task_commands_title')}</h4>
				{#if !editingTaskCmds}
					<button class="btn-icon" title={$t('tests.edit_commands')} onclick={startEditingTaskCmds}>
						<Pencil size={13} />
					</button>
				{/if}
			</div>

			{#if editingTaskCmds}
				<div class="cmd-editor">
					{#each editableCmds as cmd, i}
						<div class="cmd-edit-row">
							<input
								class="cmd-input cmd-input-name"
								placeholder={$t('tests.cmd_name_placeholder')}
								bind:value={cmd.name}
							/>
							<input
								class="cmd-input cmd-input-cmd"
								placeholder={$t('tests.cmd_command_placeholder')}
								bind:value={cmd.command}
							/>
							<button class="btn-icon btn-danger" onclick={() => removeCmd(i)} title="Remove">
								<Trash2 size={13} />
							</button>
						</div>
					{/each}
					<div class="cmd-edit-actions">
						<button class="btn btn-sm" onclick={addCmd}>
							<Plus size={13} /> {$t('tests.add_command')}
						</button>
						<div class="cmd-edit-right">
							<button class="btn btn-sm" onclick={cancelEditCmds}>{$t('tests.cancel')}</button>
							<button class="btn btn-sm btn-primary" disabled={savingCmds} onclick={saveTaskCmds}>
								{#if savingCmds}<Loader2 size={13} class="spin" />{:else}<Save size={13} />{/if}
								{$t('tests.save_commands')}
							</button>
						</div>
					</div>
				</div>
			{:else if results.task_commands && results.task_commands.length > 0}
				<CommandList commands={results.task_commands} prefix="task" />
			{:else}
				<div class="hint">{$t('tests.no_task_commands')}</div>
			{/if}
		</div>

		<!-- Summary & Actions -->
		<TestsSummary passed={results.passed} label={results.passed ? $t('tests.all_passed') : $t('tests.has_failures')} />

		<div class="tests-actions">
			{#if hasErrors}
				<button class="btn btn-primary" onclick={handleSendToLlm}>
					<Send size={14} /> {$t('tests.send_to_llm')}
				</button>
			{/if}
			<button class="btn" disabled={loading} onclick={onRunTests}>
				{#if loading}<Loader2 size={14} class="spin" />{:else}<RotateCcw size={14} />{/if}
				{$t('tests.rerun')}
			</button>
			{#if !confirmed}
				<button class="btn btn-success" onclick={onConfirm}>
					<Check size={14} /> {$t('tests.confirm')}
				</button>
			{/if}
		</div>
	{:else}
		<div class="tests-empty">
			<p>{$t('tests.not_run_yet')}</p>
		</div>
	{/if}
</div>

<style>
	.tests-panel { padding: 0.5rem 0; }
	.tests-section { margin-bottom: 1.25rem; }

	.section-header { display: flex; align-items: center; gap: 0.5rem; }

	.section-title {
		font-size: 0.8125rem; font-weight: 600; color: var(--tx);
		margin-bottom: 0.5rem; text-transform: uppercase;
		letter-spacing: 0.03em; font-family: var(--font-ui);
	}

	.section-header .section-title { margin-bottom: 0; }

	.btn-icon {
		display: inline-flex; align-items: center; justify-content: center;
		background: none; border: 1px solid var(--bd); border-radius: var(--r2);
		color: var(--dm); cursor: pointer; padding: 0.25rem;
		transition: color 0.1s, border-color 0.1s;
	}
	.btn-icon:hover { color: var(--ac); border-color: var(--ac); }
	.btn-danger:hover { color: var(--rd); border-color: var(--rd); }

	.hint { font-size: 0.8125rem; color: var(--dm); padding: 0.375rem 0; }

	/* ── Inline editor ── */
	.cmd-editor { display: flex; flex-direction: column; gap: 0.375rem; margin-top: 0.5rem; }
	.cmd-edit-row { display: flex; gap: 0.375rem; align-items: center; }

	.cmd-input {
		font-size: 0.8125rem; font-family: var(--font-mono, monospace);
		background: var(--bg2); border: 1px solid var(--bd);
		border-radius: var(--r2); color: var(--tx); padding: 0.375rem 0.5rem;
	}
	.cmd-input:focus { outline: none; border-color: var(--ac); }
	.cmd-input-name { width: 10rem; flex-shrink: 0; }
	.cmd-input-cmd { flex: 1; min-width: 0; }

	.cmd-edit-actions { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem; }
	.cmd-edit-right { margin-left: auto; display: flex; gap: 0.375rem; }
	.btn-sm { font-size: 0.75rem; padding: 0.25rem 0.625rem; }

	/* ── Actions ── */
	.tests-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }

	.btn-success {
		background: var(--gn-bright) !important; color: #fff !important;
		border-color: var(--gn-bright) !important;
	}
	.btn-success:hover { filter: brightness(1.1); }

	.tests-empty { color: var(--dm); font-size: 0.875rem; }
</style>
