<script>
	/**
	 * KITT-style scanner indicator (Knight Rider).
	 * A row of rectangular cells with a bouncing light sweep.
	 *
	 * @prop {number}  cells  — number of cells (default 12)
	 * @prop {string}  color  — accent color (default var(--ac))
	 * @prop {number}  speed  — full sweep duration in ms (default 1200)
	 * @prop {boolean} active — whether the animation is running
	 */
	let {
		cells = 12,
		color = 'var(--ac)',
		speed = 1200,
		active = true,
	} = $props();
</script>

{#if active}
	<div
		class="kitt"
		style="--kitt-color: {color}; --kitt-speed: {speed}ms; --kitt-cells: {cells};"
	>
		{#each Array(cells) as _, i}
			<div
				class="kitt-cell"
				style="--i: {i};"
			></div>
		{/each}
		<div class="kitt-sweep"></div>
	</div>
{/if}

<style>
	.kitt {
		display: flex;
		gap: 2px;
		align-items: center;
		position: relative;
		height: 10px;
		min-width: 0;
		flex-shrink: 0;
	}

	.kitt-cell {
		width: 6px;
		height: 10px;
		border-radius: 1.5px;
		background: color-mix(in srgb, var(--kitt-color) 12%, transparent);
		position: relative;
		overflow: hidden;
		flex-shrink: 0;
		transition: background 0.05s;
	}

	/* The sweep overlay — using a pseudo-element on the container */
	.kitt-sweep {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: hidden;
	}

	.kitt-sweep::after {
		content: '';
		position: absolute;
		top: 0;
		height: 100%;
		width: calc((6px + 2px) * 3); /* width of ~3 cells */
		background: radial-gradient(
			ellipse at center,
			var(--kitt-color) 0%,
			color-mix(in srgb, var(--kitt-color) 60%, transparent) 40%,
			transparent 100%
		);
		border-radius: 2px;
		filter: blur(1px);
		animation: kitt-bounce var(--kitt-speed) ease-in-out infinite;
		mix-blend-mode: screen;
	}

	/* Individual cell glow driven by the sweep position via animation */
	.kitt-cell::after {
		content: '';
		position: absolute;
		inset: 0;
		background: var(--kitt-color);
		opacity: 0;
		border-radius: inherit;
		animation: kitt-cell-glow var(--kitt-speed) ease-in-out infinite;
		animation-delay: calc(var(--i) * (var(--kitt-speed) / var(--kitt-cells) / 2));
	}

	@keyframes kitt-bounce {
		0%, 100% {
			left: -5%;
			opacity: 0.7;
		}
		50% {
			left: calc(100% - (6px + 2px) * 3);
			opacity: 1;
		}
	}

	@keyframes kitt-cell-glow {
		0%   { opacity: 0; }
		8%   { opacity: 0.9; box-shadow: 0 0 6px var(--kitt-color); }
		16%  { opacity: 0.1; }
		50%  { opacity: 0; }
		58%  { opacity: 0.9; box-shadow: 0 0 6px var(--kitt-color); }
		66%  { opacity: 0.1; }
		100% { opacity: 0; }
	}
</style>
