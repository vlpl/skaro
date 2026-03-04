<script>
	import CommandItem from '$lib/ui/CommandItem.svelte';

	let { commands = [], prefix = 'cmd' } = $props();

	let expandedCmds = $state({});

	function toggleCmd(i) {
		const key = `${prefix}-${i}`;
		expandedCmds[key] = !expandedCmds[key];
		expandedCmds = { ...expandedCmds };
	}
</script>

<div class="commands">
	{#each commands as cmd, i}
		<CommandItem
			{cmd}
			expanded={!!expandedCmds[`${prefix}-${i}`]}
			onToggle={() => toggleCmd(i)}
		/>
	{/each}
</div>

<style>
	.commands { display: flex; flex-direction: column; gap: 0.25rem; }
</style>
