/**
 * Svelte action that moves a DOM node to `document.body`.
 * Used for modals / overlays that must cover the full viewport
 * regardless of parent overflow or stacking context.
 *
 * Usage:
 *   <div use:portal>…</div>
 *
 * @param {HTMLElement} node
 */
export function portal(node) {
	document.body.appendChild(node);
	return {
		destroy() {
			node.remove();
		},
	};
}
