<script>
	import { t } from '$lib/i18n/index.js';
	import {
		CheckCircle, XCircle, CircleDot, Terminal, Send, RotateCcw,
		ChevronDown, ChevronRight, Loader2,
	} from 'lucide-svelte';

	let {
		results = null,
		loading = false,
		onRunTests = () => {},
		onSendToFix = () => {},
	} = $props();

	let expandedCmds = $state({});

	let hasErrors = $derived(results && !results.passed);
	let hasResults = $derived(results !== null);

	function toggleCmd(i) {
		const key = `global-${i}`;
		expandedCmds[key] = !expandedCmds[key];
		expandedCmds = { ...expandedCmds };
	}

	function buildErrorSummary() {
		if (!results) return '';
		const parts = [];
		for (const check of results.checklist || []) {
			if (!check.passed) parts.push(`[FAIL] ${check.label}: ${check.detail}`);
		}
		for (const cmd of results.global_commands || []) {
			if (!cmd.success) {
				const output = (cmd.stderr || cmd.stdout || '').trim();
				const truncated = output.length > 2000 ? output.slice(-2000) : output;
				parts.push(`[FAIL] ${cmd.name} (${cmd.command})\nExit code: ${cmd.exit_code}\n${truncated}`);
			}
		}
		return parts.join('\n\n---\n\n');
	}

	function handleSendToFix() {
		onSendToFix(buildErrorSummary());
	}
</script>

<div class="tests-panel">
	{#if hasResults}
		<div class="tests-section">
			<h4 class="section-title">{$t('review.checklist_title')}</h4>
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

		{#if results.global_commands && results.global_commands.length > 0}
			<div class="tests-section">
				<h4 class="section-title">{$t('review.global_commands_title')}</h4>
				<div class="commands">
					{#each results.global_commands as cmd, i}
						{@const key = `global-${i}`}
						<div class="cmd-item" class:cmd-pass={cmd.success} class:cmd-fail={!cmd.success}>
							<!-- svelte-ignore a11y_click_events_have_key_events -->
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<div class="cmd-header" onclick={() => toggleCmd(i)}>
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
									{#if cmd.stdout}<pre class="cmd-pre">{cmd.stdout}</pre>{/if}
									{#if cmd.stderr}<pre class="cmd-pre cmd-stderr">{cmd.stderr}</pre>{/if}
									{#if !cmd.stdout && !cmd.stderr}<span class="cmd-empty">{$t('tests.no_output')}</span>{/if}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<div class="tests-summary" class:summary-pass={results.passed} class:summary-fail={!results.passed}>
			<CircleDot size={16} />
			<span>{results.passed ? $t('review.all_passed') : $t('review.has_failures')}</span>
			{#if results.timestamp}
				<span class="timestamp">{new Date(results.timestamp).toLocaleString()}</span>
			{/if}
		</div>

		<div class="tests-actions">
			{#if hasErrors}
				<button class="btn btn-primary" onclick={handleSendToFix}>
					<Send size={14} /> {$t('review.send_to_fix')}
				</button>
			{/if}
			<button class="btn" disabled={loading} onclick={onRunTests}>
				{#if loading}<Loader2 size={14} class="spin" />{:else}<RotateCcw size={14} />{/if}
				{$t('review.rerun')}
			</button>
		</div>
	{:else}
		<div class="tests-empty">
			<p>{$t('review.not_run_yet')}</p>
			<button class="btn btn-primary" disabled={loading} onclick={onRunTests}>
				{#if loading}<Loader2 size={14} class="spin" />{/if}
				{$t('review.run_tests')}
			</button>
		</div>
	{/if}
</div>

<style>
	.tests-panel { padding: 0.5rem 0; }
	.tests-section { margin-bottom: 1.25rem; }

	.section-title {
		font-size: 0.8125rem; font-weight: 600; color: var(--tx);
		margin-bottom: 0.5rem; text-transform: uppercase;
		letter-spacing: 0.03em; font-family: var(--font-ui);
	}

	.check-list { display: flex; flex-direction: column; gap: 0.25rem; }

	.check-item {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.375rem 0.625rem; background: var(--bg2);
		border-radius: var(--r2); font-size: 0.8125rem;
	}

	.check-label { font-weight: 500; color: var(--tx); }

	.check-detail {
		margin-left: auto; font-size: 0.75rem;
		color: var(--dm); font-family: var(--font-ui);
	}

	:global(.icon-pass) { color: var(--gn-bright); flex-shrink: 0; }
	:global(.icon-fail) { color: var(--rd); flex-shrink: 0; }

	.commands { display: flex; flex-direction: column; gap: 0.25rem; }

	.cmd-item { background: var(--bg2); border-radius: var(--r2); overflow: hidden; }

	.cmd-header {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.375rem 0.625rem; cursor: pointer;
		font-size: 0.8125rem; color: var(--tx); transition: background 0.1s;
	}
	.cmd-header:hover { background: var(--sf2); }
	.cmd-name { font-weight: 500; }

	.cmd-code {
		font-size: 0.6875rem; color: var(--dm); background: var(--bg3);
		padding: 0.0625rem 0.375rem; border-radius: 0.1875rem;
		font-family: var(--font-mono, monospace);
	}

	.cmd-exit {
		margin-left: auto; font-size: 0.6875rem;
		color: var(--dm); font-family: var(--font-ui);
	}

	.cmd-output {
		padding: 0.5rem 0.625rem; border-top: 1px solid var(--bd);
		max-height: 20rem; overflow-y: auto;
	}

	.cmd-pre {
		font-size: 0.75rem; font-family: var(--font-mono, monospace);
		white-space: pre-wrap; word-break: break-all;
		color: var(--tx); margin: 0; line-height: 1.5;
	}

	.cmd-stderr { color: var(--rd); }
	.cmd-empty { font-size: 0.75rem; color: var(--dm); }

	.tests-summary {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.625rem 0.75rem; border-radius: var(--r);
		font-size: 0.875rem; font-weight: 600; margin-bottom: 0.75rem;
	}
	.tests-summary.summary-pass { background: rgba(106, 135, 89, 0.15); color: var(--gn-bright); }
	.tests-summary.summary-fail { background: rgba(207, 106, 76, 0.15); color: var(--rd); }

	.timestamp { margin-left: auto; font-size: 0.75rem; font-weight: 400; opacity: 0.7; }

	.tests-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }

	.tests-empty {
		color: var(--dm); font-size: 0.875rem;
		display: flex; flex-direction: column; align-items: center;
		gap: 1rem; padding: 2rem 0;
	}
</style>
