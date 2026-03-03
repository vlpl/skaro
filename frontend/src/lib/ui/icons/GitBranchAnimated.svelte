<!-- GitBranchAnimated.svelte -->
<script lang="ts">
  export let size: number = 24;
  export let duration: number = 420;
  export let active: boolean = false;
  export let ariaLabel: string = 'Git Branch';
  export let title: string | null = null;
  export let className: string = '';
</script>

<svg
  class={`gitAnim ${active ? 'is-active' : ''} ${className}`}
  style={`--ga-size:${size}px; --ga-dur:${duration}ms;`}
  xmlns="http://www.w3.org/2000/svg"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  role="img"
  aria-label={ariaLabel}
>
  {#if title}<title>{title}</title>{/if}

  <!-- Trunk: line between circle edges, not through them -->
  <line x1="6" y1="9" x2="6" y2="15" />
  <circle cx="6" cy="6" r="3" />
  <circle cx="6" cy="18" r="3" />

  <!-- Second branch (always visible): edge-to-edge -->
  <path d="M18 9a9 9 0 0 1-9 9" />
  <circle cx="18" cy="6" r="3" />

  <!-- Third branch: unfolds clockwise from bottom-left circle on hover -->
  <g class="fold-branch">
    <path d="M6 21C6 24 12 21 15 21" />
    <circle cx="18" cy="21" r="3" />
  </g>
</svg>

<style>
  .gitAnim {
    width: var(--ga-size);
    height: var(--ga-size);
    overflow: visible;
    --ease: cubic-bezier(.4, 0, .2, 1);
  }

  .fold-branch {
    transform-origin: 25% 75%; /* (6,18) — bottom-left circle center */
    transform: rotate(-90deg);
    opacity: 0;
    transition:
      transform var(--ga-dur) var(--ease),
      opacity calc(var(--ga-dur) * 0.35) var(--ease);
    will-change: transform, opacity;
  }

  .gitAnim:is(:hover, .is-active) .fold-branch {
    transform: rotate(0deg);
    opacity: 1;
    transition:
      transform var(--ga-dur) var(--ease),
      opacity calc(var(--ga-dur) * 0.25) var(--ease);
  }

  @media (prefers-reduced-motion: reduce) {
    .fold-branch { transition: none; }
    .gitAnim:is(:hover, .is-active) .fold-branch {
      transform: rotate(0deg);
      opacity: 1;
    }
  }
</style>