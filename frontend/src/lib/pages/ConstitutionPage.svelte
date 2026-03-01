<script>
	import { onMount } from 'svelte';
	import { t } from '$lib/i18n/index.js';
	import { api } from '$lib/api/client.js';
	import { addLog, addError } from '$lib/stores/logStore.js';
	import { cachedFetch, invalidate } from '$lib/api/cache.js';
	import { status } from '$lib/stores/statusStore.js';
	import { FileText, AlertTriangle, CheckCircle, XCircle, Loader2, Pencil } from 'lucide-svelte';
	import MarkdownContent from '$lib/ui/MarkdownContent.svelte';
	import MdEditor from '$lib/ui/md-editor/MdEditor.svelte';

	let data = $state(null);
	let validation = $state(null);
	let validating = $state(false);
	let error = $state('');
	let showEditor = $state(false);

	onMount(() => { load(); });

	async function load() {
		try { data = await cachedFetch('constitution', () => api.getConstitution()); }
		catch (e) { error = e.message; addError(e.message, 'constitution'); }
	}

	async function validate() {
		validating = true; validation = null;
		addLog($t('log.validating'));
		try {
			validation = await api.validateConstitution();
			addLog(validation.valid ? $t('log.validation_passed') : $t('log.validation_issues'));
		} catch (e) { addError(e.message, 'validateConstitution'); error = e.message; }
		validating = false;
	}

	async function saveContent(text) {
		try {
			await api.saveConstitution(text);
			invalidate('constitution', 'status');
			status.set(await api.getStatus());
			await load();
			addLog($t('editor.doc_saved'));
			showEditor = false;
		} catch (e) { addError(e.message, 'constitutionSave'); throw e; }
	}
</script>

<div class="main-header">
	<h2><FileText size={24} /> {$t('const.title')}</h2>
	<p>{$t('const.subtitle')}</p>
</div>

{#if error}
	<div class="alert alert-warn"><AlertTriangle size={14} /> {error}</div>
{:else if !data}
	<div class="loading-text"><Loader2 size={14} class="spin" /> {$t('app.loading')}</div>
{:else}
	{#if !data.has_constitution}
		<div class="alert alert-warn"><AlertTriangle size={14} /> {$t('const.empty')}</div>
		<div class="instructions">
			<h4>{$t('const.next_steps')}</h4>
			<ol>
				<li>{$t('const.step1', { file: '.skaro/constitution.md' })}</li>
				<li>{$t('const.step2')}</li>
				<li>{$t('const.step3')}</li>
			</ol>
		</div>
	{:else}
		<div class="btn-group">
			<button class="btn btn-primary" disabled={validating} onclick={validate}>
				{#if validating}<Loader2 size={14} class="spin" />{:else}<CheckCircle size={14} />{/if}
				{$t('const.validate')}
			</button>
			<button class="btn" onclick={() => showEditor = true}>
				<Pencil size={14} /> {$t('editor.edit')}
			</button>
		</div>
	{/if}

	{#if validation}
		{#if validation.valid}
			<div class="alert alert-success"><CheckCircle size={14} /> {$t('const.valid')}</div>
		{:else}
			<div class="alert alert-warn"><AlertTriangle size={14} /> {$t('const.invalid')}</div>
		{/if}
		<ul class="check-list">
			{#each Object.entries(validation.checks) as [section, ok]}
				<li>
					{#if ok}<CheckCircle size={14} color="var(--gn-bright)" />{:else}<XCircle size={14} color="var(--rd)" />{/if}
					{section.replace(/_/g, ' ')}
				</li>
			{/each}
		</ul>
	{/if}

	{#if data.content}
        <MarkdownContent content={data.content} />
	{/if}

	{#if showEditor}
		<MdEditor
			content={data.content || ''}
			onSave={saveContent}
			onClose={() => showEditor = false}
		/>
	{/if}
{/if}
