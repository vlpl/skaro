<!-- FolderOpenCrossfade.svelte -->
<script lang="ts">
  export let size: number = 24;        // px
  export let fade: number = 180;       // ms (кроссфейд)
  export let active: boolean = false;  // программный запуск как hover
  export let ariaLabel: string = 'Folder';
  export let title: string | null = null;
  export let className: string = '';

  // лёгкий “параллакс” при переключении (можешь оставить дефолт)
  export let shiftY: number = 0.6;     // px
  export let scaleFrom: number = 0.99; // open start scale
  export let scaleTo: number = 1.01;   // closed hover scale
</script>

<svg
  class={`folderAnim ${active ? 'is-active' : ''} ${className}`}
  style={`--fa-size:${size}px; --fa-fade:${fade}ms; --fa-shiftY:${shiftY}px; --fa-scaleFrom:${scaleFrom}; --fa-scaleTo:${scaleTo};`}
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

  <!-- CLOSED -->
  <g class="state closed">
    <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
    <path d="M2 10h20"/>
  </g>

  <!-- OPEN -->
  <g class="state open">
    <path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"/>
  </g>
</svg>

<style>
  .folderAnim{
    width: var(--fa-size);
    height: var(--fa-size);
    --ease: cubic-bezier(.2,.9,.2,1);
  }

  .state{
    transform-origin: center;
    transition:
      opacity var(--fa-fade) var(--ease),
      transform var(--fa-fade) var(--ease);
    will-change: opacity, transform;
  }

  /* default */
  .closed{
    opacity: 1;
    transform: translateY(0) scale(1);
  }

  .open{
    opacity: 0;
    transform: translateY(var(--fa-shiftY)) scale(var(--fa-scaleFrom));
  }

  /* hover / active: crossfade */
  .folderAnim:is(:hover, .is-active) .closed{
    opacity: 0;
    transform: translateY(calc(-1 * var(--fa-shiftY))) scale(var(--fa-scaleTo));
  }

  .folderAnim:is(:hover, .is-active) .open{
    opacity: 1;
    transform: translateY(0) scale(1);
  }

  @media (prefers-reduced-motion: reduce){
    .state{ transition: none; }
    .folderAnim:is(:hover, .is-active) .closed{ opacity: 0; transform: none; }
    .folderAnim:is(:hover, .is-active) .open{ opacity: 1; transform: none; }
  }
</style>