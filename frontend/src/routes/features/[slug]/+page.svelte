<script>
	import { page } from '$app/stores';
	import FeatureDetailPage from '$lib/pages/FeatureDetailPage.svelte';

	let slug = $derived(decodeURIComponent($page.params.slug));
</script>

<FeatureDetailPage {slug} />
