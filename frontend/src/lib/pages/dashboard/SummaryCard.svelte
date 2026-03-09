<script>
	/** @type {import('svelte').Component} */
	let { icon: Icon, label, value } = $props();
</script>

<div class="widget card sm summary-card">
	<div class="sc-value">{value}</div>
	<div class="sc-label"><Icon size={16} /> {label}</div>
</div>

<style>
	.summary-card {
		border-radius: var(--r);
		padding: 1rem 0.75rem;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.sc-value {
		font-size: 1.625rem;
		font-weight: 700;
		color: var(--tx-bright);
		font-family: var(--font-ui);
		line-height: 1.1;
	}

	.sc-label {
		font-size: .75rem;
		color: var(--tx);
		margin-top: 0.375rem;
		text-transform: uppercase;
		letter-spacing: 0.018rem;
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
	}
</style>
