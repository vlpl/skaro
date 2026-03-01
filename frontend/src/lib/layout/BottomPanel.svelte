<script>
	import { t } from '$lib/i18n/index.js';
	import { page } from '$app/stores';
	import { logEntries, errorEntries, clearLog, clearErrors, llmActive } from '$lib/stores/logStore.js';
	import { status, wsConnected } from '$lib/stores/statusStore.js';
	import { Play, AlertTriangle, Trash2, ChevronUp, ChevronDown, Cpu } from 'lucide-svelte';
	import LogPane from './LogPane.svelte';
	import ErrorPane from './ErrorPane.svelte';

	const TAB_ROLES = {
		constitution: null,
		architecture: 'architect',
		adr: 'architect',
		devplan: 'architect',
		tasks: 'coder',
		settings: null,
	};

	let activePane = $state('run');
	let panelEl = $state(null);

	const STORAGE_KEY = 'skaro:bottom-panel-collapsed';

	function readStored() {
		try {
			const v = sessionStorage.getItem(STORAGE_KEY);
			return v === null ? true : v === '1';
		}
		catch { return true; }
	}
	function writeStored(v) {
		try { sessionStorage.setItem(STORAGE_KEY, v ? '1' : '0'); }
		catch { /* noop */ }
	}

	let storedCollapsed = $state(readStored());
	let dashboardOverride = $state(/** @type {boolean|null} */ (null));
	let savedHeight = $state(200);

	// ── LLM auto-open/close ──
	let llmOverride = $state(/** @type {boolean|null} */ (null));
	let wasCollapsedBeforeLlm = $state(true);
	let prevLlmActive = $state(false);

	/** CSS transition enabled only during LLM-driven open/close */
	let animating = $state(false);
	let animTimer = $state(null);

	function enableAnim() {
		animating = true;
		if (animTimer) clearTimeout(animTimer);
		// Remove class after transition completes
		animTimer = setTimeout(() => { animating = false; animTimer = null; }, 350);
	}

	$effect(() => {
		const active = $llmActive;
		if (active && !prevLlmActive) {
			// LLM just started
			wasCollapsedBeforeLlm = collapsed;
			enableAnim();
			llmOverride = false;
			activePane = 'run';
		} else if (!active && prevLlmActive) {
			// LLM just ended
			if (wasCollapsedBeforeLlm) {
				setTimeout(() => { enableAnim(); llmOverride = null; }, 1500);
			} else {
				llmOverride = null;
			}
		}
		prevLlmActive = active;
	});

	let currentTab = $derived.by(() => {
		const parts = $page.url.pathname.split('/').filter(Boolean);
		return parts[0] || 'dashboard';
	});

	let onDashboard = $derived(currentTab === 'dashboard');

	function getRoleInfo(s, tab) {
		if (!s?.config) return '—';
		const roleName = TAB_ROLES[tab];
		const cfg = s.config;
		if (roleName && cfg.roles?.[roleName]) {
			const r = cfg.roles[roleName];
			const label = $t('settings.role_' + roleName);
			return `${label}: ${r.provider} / ${r.model}`;
		}
		const label = $t('status.role_default');
		return `${label}: ${cfg.llm_provider} / ${cfg.llm_model}`;
	}

	let prevTab = $state('');
	$effect(() => {
		if (currentTab !== prevTab) {
			dashboardOverride = null;
			prevTab = currentTab;
		}
	});

	let collapsed = $derived(
		llmOverride !== null
			? llmOverride
			: (onDashboard
				? (dashboardOverride !== null ? dashboardOverride : true)
				: storedCollapsed)
	);

	function onMouseDown(e) {
		e.preventDefault();
		const startY = e.clientY;
		const startH = panelEl?.offsetHeight ?? 200;
		function onMove(ev) {
			const delta = startY - ev.clientY;
			const newH = Math.min(Math.max(startH + delta, 80), window.innerHeight * 0.6);
			if (panelEl) panelEl.style.height = newH + 'px';
			savedHeight = newH;
		}
		function onUp() {
			document.removeEventListener('mousemove', onMove);
			document.removeEventListener('mouseup', onUp);
		}
		document.addEventListener('mousemove', onMove);
		document.addEventListener('mouseup', onUp);
	}

	function switchPane(pane) {
		activePane = pane;
		if (collapsed) {
			if (onDashboard) dashboardOverride = false;
			else { storedCollapsed = false; writeStored(false); }
		}
	}

	function toggle() {
		llmOverride = null;
		const next = !collapsed;
		if (onDashboard) {
			dashboardOverride = next;
		} else {
			storedCollapsed = next;
			writeStored(next);
		}
	}

	function handleClear() {
		if (activePane === 'run') clearLog();
		else clearErrors();
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="resize-handle" onmousedown={onMouseDown}></div>

<div
	class="bottom-panel"
	class:collapsed
	class:animating
	bind:this={panelEl}
	style="height: {collapsed ? '28px' : savedHeight + 'px'}"
>
	<div class="tabs-bar">
		<span class="bp-info ws-status">
			<span class="status-dot" class:off={!$wsConnected}></span>
			<span>{$wsConnected ? $t('status.connected') : $t('status.disconnected')}</span>
		</span>
		<span class="bp-separator"></span>
		<button class="bp-tab" class:active={activePane === 'run'} onclick={() => switchPane('run')}>
			<Play size={12} /> {$t('panel.run')}
			{#if $llmActive}
				<span class="llm-dot"></span>
			{:else}
				<span class="count">{$logEntries.length}</span>
			{/if}
		</button>
		<button class="bp-tab" class:active={activePane === 'errors'} onclick={() => switchPane('errors')}>
			<AlertTriangle size={12} /> {$t('panel.problems')} <span class="count" class:has-errors={$errorEntries.length > 0}>{$errorEntries.length}</span>
		</button>
		<button class="icon-btn" onclick={handleClear} title={$t('panel.clear')}><Trash2 size={13} /></button>
		<div class="tab-actions">
			<span class="bp-info model-info">
				<Cpu size={11} />
				<span>{getRoleInfo($status, currentTab)}</span>
			</span>
			<button class="icon-btn" onclick={toggle} title={$t('panel.minimize')}>
				{#if collapsed}<ChevronUp size={14} />{:else}<ChevronDown size={14} />{/if}
			</button>
		</div>
	</div>

	{#if !collapsed}
		<div class="panel-content">
			{#if activePane === 'run'}
				<LogPane />
			{:else}
				<ErrorPane />
			{/if}
		</div>
	{/if}
</div>

<style>
	.resize-handle {
		height: 0.1875rem;
		background: transparent;
		cursor: ns-resize;
		flex-shrink: 0;
		transition: background .15s;
		border-top: 0.125rem solid transparent;
	}

	.resize-handle:hover {
		background: var(--ac);
	}

	.bottom-panel {
		background: var(--bg2);
		border-top: 0.0625rem solid var(--bd);
		display: flex;
		flex-direction: column;
		flex-shrink: 0;
		min-height: 1.75rem;
		max-height: 60vh;
		overflow: hidden;
		/* No transition by default — instant resize */
	}

	/* Smooth transition ONLY during LLM auto-open/close */
	.bottom-panel.animating {
		transition: height 0.3s ease-out;
	}

	.tabs-bar {
		display: flex;
		align-items: center;
		height: 1.75rem;
		background: var(--sf);
		border-bottom: 0.0625rem solid var(--bd);
		flex-shrink: 0;
		padding: 0 0.25rem;
		user-select: none;
	}

	.bp-tab {
		display: flex;
		align-items: center;
		gap: 0.3125rem;
		padding: 0 0.75rem;
		height: 1.75rem;
		font-size: 0.8125rem;
		color: var(--dm);
		cursor: pointer;
		border: none;
		border-bottom: 0.125rem solid transparent;
		background: none;
		font-family: inherit;
		transition: color .1s;
	}

	.bp-info {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0 0.625rem;
		height: 1.75rem;
		font-size: 0.75rem;
		color: var(--tx);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		flex-shrink: 0;
	}

	.model-info {
		flex-shrink: 1;
		min-width: 0;
	}

	.ws-status {
		flex-shrink: 0;
	}

	.status-dot {
		width: 0.375rem;
		height: 0.375rem;
		border-radius: 50%;
		background: #00de39;
		flex-shrink: 0;
	}

	.status-dot.off {
		background: #ff4200;
	}

	.bp-separator {
		width: 0.0625rem;
		height: 0.875rem;
		background: var(--bd);
		flex-shrink: 0;
		margin: 0 0.125rem;
	}

	.bp-tab:hover { color: var(--tx); }

	.bp-tab.active {
		color: var(--tx-bright);
		border-bottom-color: var(--ac);
	}

	.count {
		background: var(--bg2);
		padding: 0 0.3125rem;
		border-radius: 0.375rem;
		font-size: 0.6875rem;
		font-family: var(--font-ui);
		line-height: 1rem;
	}

	.count.has-errors {
		background: var(--rd-dim);
		color: #fff;
	}

	.llm-dot {
		width: 0.4375rem;
		height: 0.4375rem;
		border-radius: 50%;
		background: var(--ac);
		animation: llm-pulse 1s ease-in-out infinite;
	}

	@keyframes llm-pulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.4; transform: scale(0.7); }
	}

	.tab-actions {
		margin-left: auto;
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding-right: 0.25rem;
	}

	.icon-btn {
		width: 1.375rem;
		height: 1.375rem;
		display: flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: none;
		color: var(--dm);
		cursor: pointer;
		border-radius: 0.125rem;
	}

	.icon-btn:hover {
		background: var(--sf2);
		color: var(--tx);
	}

	.panel-content {
		flex: 1;
		overflow-y: auto;
		font-family: var(--font-ui);
		font-size: 0.8125rem;
	}
</style>
