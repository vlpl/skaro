<script>
	import { t } from '$lib/i18n/index.js';
	import { api } from '$lib/api/client.js';
	import { status } from '$lib/stores/statusStore.js';
	import { addLog } from '$lib/stores/logStore.js';
	import { Sparkles } from 'lucide-svelte';
	import FixChat from '$lib/ui/FixChat.svelte';

	let modelDisplay = $derived.by(() => {
		const s = $status;
		if (!s?.config) return '';
		const cfg = s.config;
		if (cfg.roles?.architect) return `${cfg.roles.architect.provider} / ${cfg.roles.architect.model}`;
		return `${cfg.llm_provider} / ${cfg.llm_model}`;
	});

	function loadConversationFn() {
		return api.loadFeatureConversation();
	}

	function sendMessageFn(text, history, signal) {
		return api.sendFeatureMessage(text, history, signal);
	}

	function applyFileFn(filepath, content) {
		return api.applyFeatureArtifact(filepath, content);
	}

	function clearConversationFn() {
		return api.clearFeatureConversation();
	}

	function onSendSuccess() {
		addLog($t('log.feature_response'));
	}
</script>

<div class="main-header">
	<h2><Sparkles size={24} /> {$t('feature.title')}</h2>
	<p>{$t('feature.subtitle')}</p>
</div>

<FixChat
	{modelDisplay}
	placeholder={$t('feature.placeholder')}
	errorSource="feature"
	scopeEnabled={false}
	{loadConversationFn}
	{sendMessageFn}
	{applyFileFn}
	{clearConversationFn}
	{onSendSuccess}
/>
