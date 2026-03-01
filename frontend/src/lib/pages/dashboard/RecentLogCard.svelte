<script>
	import { t } from '$lib/i18n/index.js';
	import { fmt } from '$lib/utils/format.js';

	let { entries = [] } = $props();
</script>

<div class="widget lg card">
	<h3>{$t('stats.recent_log')}</h3>
	{#if entries?.length}
		<div class="log-scroll">
			<table class="stat-table log-table">
				<thead>
					<tr>
						<th class="al">{$t('stats.col_time')}</th>
						<th class="al">{$t('stats.col_phase')}</th>
						<th class="al">{$t('stats.col_task')}</th>
						<th class="al">{$t('stats.col_model')}</th>
						<th class="ar">In</th>
						<th class="ar">Out</th>
					</tr>
				</thead>
				<tbody>
					{#each entries as e}
						<tr>
							<td class="al mono">{e.ts?.slice(11, 19) || ''}</td>
							<td class="al">{e.phase}</td>
							<td class="al">{e.task || '—'}</td>
							<td class="al mono">{e.model}</td>
							<td class="ar num">{fmt(e.input_tokens)}</td>
							<td class="ar num">{fmt(e.output_tokens)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<p class="empty-hint">{$t('dash.no_data')}</p>
	{/if}
</div>
