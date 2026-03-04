<script>
	import { CircleDot } from 'lucide-svelte';

	let { passed = false, label = '', timestamp = '' } = $props();
</script>

<div class="tests-summary" class:summary-pass={passed} class:summary-fail={!passed}>
	<CircleDot size={16} />
	<span>{label}</span>
	{#if timestamp}
		<span class="timestamp">{new Date(timestamp).toLocaleString()}</span>
	{/if}
</div>

<style>
	.tests-summary {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.625rem 0.75rem; border-radius: var(--r);
		font-size: 0.875rem; font-weight: 600; margin-bottom: 0.75rem;
	}
	.tests-summary.summary-pass { background: rgba(106, 135, 89, 0.15); color: var(--gn-bright); }
	.tests-summary.summary-fail { background: rgba(207, 106, 76, 0.15); color: var(--rd); }
	.timestamp { margin-left: auto; font-size: 0.75rem; font-weight: 400; opacity: 0.7; }
</style>
