<!-- ShieldCheckAnimated.svelte -->
<script lang="ts">
  export let size: number = 24;
  export let duration: number = 420;
  export let active: boolean = false;
  export let ariaLabel: string = 'Review';
  export let title: string | null = null;
  export let className: string = '';
</script>

<svg
  class={`shieldAnim ${active ? 'is-active' : ''} ${className}`}
  style={`--sa-size:${size}px; --sa-dur:${duration}ms;`}
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

  <!-- Shield body -->
  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />

  <!-- Checkmark: draws in on hover -->
  <polyline class="check" points="9 12 11 14 15 10" />
</svg>

<style>
  .shieldAnim {
    width: var(--sa-size);
    height: var(--sa-size);
    overflow: visible;
    --ease: cubic-bezier(.4, 0, .2, 1);
  }

  .check {
    stroke-dasharray: 12;
    stroke-dashoffset: 12;
    transition: stroke-dashoffset var(--sa-dur) var(--ease);
    will-change: stroke-dashoffset;
  }

  .shieldAnim:is(:hover, .is-active) .check {
    stroke-dashoffset: 0;
  }

  @media (prefers-reduced-motion: reduce) {
    .check { transition: none; }
    .shieldAnim:is(:hover, .is-active) .check {
      stroke-dashoffset: 0;
    }
  }
</style>
