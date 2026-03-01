<script>
	import { page } from '$app/stores';
	import { api } from '$lib/api/client.js';
	import { taskDetail } from '$lib/stores/statusStore.js';
	import { addError } from '$lib/stores/logStore.js';
	import { cachedFetch } from '$lib/api/cache.js';
	import TaskDetail from '$lib/pages/tasks/TaskDetail.svelte';

	let taskName = $derived(decodeURIComponent($page.params.name));

	$effect(() => {
		if (taskName) {
			loadDetail(taskName);
		}
	});

	async function loadDetail(name) {
		try {
			taskDetail.set(await cachedFetch(`task:${name}`, () => api.getTask(name)));
		} catch (e) {
			addError(e.message, 'loadTaskDetail');
		}
	}
</script>

<TaskDetail {taskName} />
