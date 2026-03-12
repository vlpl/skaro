<script>
	import { t } from '$lib/i18n/index.js';
	import { fmt, totalTok, sorted } from '$lib/utils/format.js';

	/** @type {import('svelte').Component} */
	let { icon: Icon, title, data = {}, size = 'md' } = $props();

	let rows = $derived(sorted(data));
</script>

<div class="widget {size} card">
	<h3><Icon size={16} /> {title}</h3>
	{#if rows.length}
		<div class="log-scroll">
			<table class="stat-table">
				<thead>
					<tr>
						<th class="al">{$t('stats.col_name')}</th>
						<th class="ar">{$t('stats.col_requests')}</th>
						<th class="ar">{$t('stats.col_tokens')}</th>
					</tr>
				</thead>
				<tbody>
					{#each rows as [name, d]}
						<tr>
							<td class="al name">{name}</td>
							<td class="ar num">{d.requests}</td>
							<td class="ar num">{fmt(totalTok(d))}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<p class="empty-hint">{$t('dash.no_data')}</p>
	{/if}
</div>
