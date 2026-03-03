<script>
	import { t } from '$lib/i18n/index.js';
	import { api } from '$lib/api/client.js';
	import { addLog, addError } from '$lib/stores/logStore.js';
	import {
		CheckCircle, XCircle, CircleDot, Terminal, Send, RotateCcw,
		ChevronDown, ChevronRight, Check, Loader2, Pencil, Plus, Trash2, Save,
	} from 'lucide-svelte';

	let {
		taskName = '',
		results = null,
		loading = false,
		confirmed = false,
		onRunTests = () => {},
		onConfirm = () => {},
		onSendToLlm = () => {},
	} = $props();

	let expandedCmds = $state({});
	let editingTaskCmds = $state(false);
	let editableCmds = $state([]);
	let savingCmds = $state(false);

	let hasErrors = $derived(results && !results.passed);
	let hasResults = $derived(results !== null);

	function toggleCmd(section, i) {
		const key = `${section}-${i}`;
		expandedCmds[key] = !expandedCmds[key];
		expandedCmds = { ...expandedCmds };
	}

	// ── Inline editing ──

	async function startEditingTaskCmds() {
		try {
			const data = await api.getVerifyCommands(taskName);
			editableCmds = (data.commands || []).map((c) => ({ ...c }));
		} catch {
			// If no commands yet, start with empty list
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

	// ── Error summary for LLM ──

	function buildErrorSummary() {
		if (!results) return '';
		const parts = [];

		for (const check of results.checklist || []) {
			if (!check.passed) {
				parts.push(`[FAIL] ${check.label}: ${check.detail}`);
			}
		}
		for (const cmd of (results.task_commands || [])) {
			if (!cmd.success) {
				const output = (cmd.stderr || cmd.stdout || '').trim();
				const truncated = output.length > 2000 ? output.slice(-2000) : output;
				parts.push(`[FAIL] ${cmd.name} (${cmd.command})\nExit code: ${cmd.exit_code}\n${truncated}`);
			}
		}
		return parts.join('\n\n---\n\n');
	}

	function handleSendToLlm() {
		onSendToLlm(buildErrorSummary());
	}
</script>

<div class="tests-panel">
	{#if hasResults}
		<!-- ═══ Checklist ═══ -->
		<div class="tests-section">
			<h4 class="section-title">{$t('tests.checklist_title')}</h4>
			<div class="check-list">
				{#each results.checklist as check}
					<div class="check-item" class:pass={check.passed} class:fail={!check.passed}>
						{#if check.passed}
							<CheckCircle size={15} class="icon-pass" />
						{:else}
							<XCircle size={15} class="icon-fail" />
						{/if}
						<span class="check-label">{check.label}</span>
						<span class="check-detail">{check.detail}</span>
					</div>
				{/each}
			</div>
		</div>

		<!-- ═══ Task commands (from plan / verify.yaml) ═══ -->
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
				<!-- Inline editor -->
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
				<div class="commands">
					{#each results.task_commands as cmd, i}
						{@const key = `task-${i}`}
						{@render commandItem(cmd, key, 'task', i)}
					{/each}
				</div>
			{:else}
				<div class="hint">{$t('tests.no_task_commands')}</div>
			{/if}
		</div>

		<!-- ═══ Summary & Actions ═══ -->
		<div class="tests-summary" class:summary-pass={results.passed} class:summary-fail={!results.passed}>
			<CircleDot size={16} />
			<span>{results.passed ? $t('tests.all_passed') : $t('tests.has_failures')}</span>
		</div>

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

<!-- ═══ Command item snippet ═══ -->
{#snippet commandItem(cmd, key, section, i)}
	<div class="cmd-item" class:cmd-pass={cmd.success} class:cmd-fail={!cmd.success}>
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="cmd-header" onclick={() => toggleCmd(section, i)}>
			{#if cmd.success}
				<CheckCircle size={15} class="icon-pass" />
			{:else}
				<XCircle size={15} class="icon-fail" />
			{/if}
			<Terminal size={13} />
			<span class="cmd-name">{cmd.name}</span>
			<code class="cmd-code">{cmd.command}</code>
			<span class="cmd-exit">exit {cmd.exit_code}</span>
			{#if expandedCmds[key]}
				<ChevronDown size={14} />
			{:else}
				<ChevronRight size={14} />
			{/if}
		</div>
		{#if expandedCmds[key]}
			<div class="cmd-output">
				{#if cmd.stdout}
					<pre class="cmd-pre">{cmd.stdout}</pre>
				{/if}
				{#if cmd.stderr}
					<pre class="cmd-pre cmd-stderr">{cmd.stderr}</pre>
				{/if}
				{#if !cmd.stdout && !cmd.stderr}
					<span class="cmd-empty">{$t('tests.no_output')}</span>
				{/if}
			</div>
		{/if}
	</div>
{/snippet}

<style>
	.tests-panel {
		padding: 0.5rem 0;
	}

	.tests-section {
		margin-bottom: 1.25rem;
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.section-title {
		font-size: 0.8125rem;
		font-weight: 600;
		color: var(--tx);
		margin-bottom: 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		font-family: var(--font-ui);
	}

	.section-header .section-title {
		margin-bottom: 0;
	}

	.btn-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: 1px solid var(--bd);
		border-radius: var(--r2);
		color: var(--dm);
		cursor: pointer;
		padding: 0.25rem;
		transition: color 0.1s, border-color 0.1s;
	}

	.btn-icon:hover {
		color: var(--ac);
		border-color: var(--ac);
	}

	.btn-danger:hover {
		color: var(--rd);
		border-color: var(--rd);
	}

	.hint {
		font-size: 0.8125rem;
		color: var(--dm);
		padding: 0.375rem 0;
	}

	/* ── Checklist ── */
	.check-list {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.check-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.375rem 0.625rem;
		background: var(--bg2);
		border-radius: var(--r2);
		font-size: 0.8125rem;
	}

	.check-label {
		font-weight: 500;
		color: var(--tx);
	}

	.check-detail {
		margin-left: auto;
		font-size: 0.75rem;
		color: var(--dm);
		font-family: var(--font-ui);
	}

	:global(.icon-pass) { color: var(--gn-bright); flex-shrink: 0; }
	:global(.icon-fail) { color: var(--rd); flex-shrink: 0; }

	/* ── Commands ── */
	.commands {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.cmd-item {
		background: var(--bg2);
		border-radius: var(--r2);
		overflow: hidden;
	}

	.cmd-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.375rem 0.625rem;
		cursor: pointer;
		font-size: 0.8125rem;
		color: var(--tx);
		transition: background 0.1s;
	}

	.cmd-header:hover {
		background: var(--sf2);
	}

	.cmd-name {
		font-weight: 500;
	}

	.cmd-code {
		font-size: 0.6875rem;
		color: var(--dm);
		background: var(--bg3);
		padding: 0.0625rem 0.375rem;
		border-radius: 0.1875rem;
		font-family: var(--font-mono, monospace);
	}

	.cmd-exit {
		margin-left: auto;
		font-size: 0.6875rem;
		color: var(--dm);
		font-family: var(--font-ui);
	}

	.cmd-output {
		padding: 0.5rem 0.625rem;
		border-top: 1px solid var(--bd);
		max-height: 20rem;
		overflow-y: auto;
	}

	.cmd-pre {
		font-size: 0.75rem;
		font-family: var(--font-mono, monospace);
		white-space: pre-wrap;
		word-break: break-all;
		color: var(--tx);
		margin: 0;
		line-height: 1.5;
	}

	.cmd-stderr { color: var(--rd); }
	.cmd-empty { font-size: 0.75rem; color: var(--dm); }

	/* ── Inline editor ── */
	.cmd-editor {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		margin-top: 0.5rem;
	}

	.cmd-edit-row {
		display: flex;
		gap: 0.375rem;
		align-items: center;
	}

	.cmd-input {
		font-size: 0.8125rem;
		font-family: var(--font-mono, monospace);
		background: var(--bg2);
		border: 1px solid var(--bd);
		border-radius: var(--r2);
		color: var(--tx);
		padding: 0.375rem 0.5rem;
	}

	.cmd-input:focus {
		outline: none;
		border-color: var(--ac);
	}

	.cmd-input-name {
		width: 10rem;
		flex-shrink: 0;
	}

	.cmd-input-cmd {
		flex: 1;
		min-width: 0;
	}

	.cmd-edit-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.25rem;
	}

	.cmd-edit-right {
		margin-left: auto;
		display: flex;
		gap: 0.375rem;
	}

	.btn-sm {
		font-size: 0.75rem;
		padding: 0.25rem 0.625rem;
	}

	/* ── Summary ── */
	.tests-summary {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 0.75rem;
		border-radius: var(--r);
		font-size: 0.875rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
	}

	.tests-summary.summary-pass {
		background: rgba(106, 135, 89, 0.15);
		color: var(--gn-bright);
	}

	.tests-summary.summary-fail {
		background: rgba(207, 106, 76, 0.15);
		color: var(--rd);
	}

	/* ── Actions ── */
	.tests-actions {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.btn-success {
		background: var(--gn-bright) !important;
		color: #fff !important;
		border-color: var(--gn-bright) !important;
	}

	.btn-success:hover { filter: brightness(1.1); }

	.tests-empty {
		color: var(--dm);
		font-size: 0.875rem;
	}
</style>
