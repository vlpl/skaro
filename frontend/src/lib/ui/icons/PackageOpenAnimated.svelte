<!-- PackageOpenAnimated.svelte -->
<script lang="ts">
  export let size: number = 24;       // px
  export let fade: number = 140;      // ms (переключение состояний)
  export let draw: number = 420;      // ms (дорисовка open)
  export let active: boolean = false; // программный запуск как hover
  export let ariaLabel: string = 'Package';
  export let title: string | null = null;
  export let className: string = '';
</script>

<svg
  class={`pkgAnim ${active ? 'is-active' : ''} ${className}`}
  style={`--pa-size:${size}px; --pa-fade:${fade}ms; --pa-draw:${draw}ms;`}
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
    <path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/>
    <path d="M12 22V12"/>
    <polyline points="3.29 7 12 12 20.71 7"/>
    <path d="m7.5 4.27 9 5.15"/>
  </g>

  <!-- OPEN -->
  <g class="state open">
    <path class="o o1" pathLength="100" d="M12 22v-9"/>
    <path class="o o2" pathLength="100" d="M15.17 2.21a1.67 1.67 0 0 1 1.63 0L21 4.57a1.93 1.93 0 0 1 0 3.36L8.82 14.79a1.655 1.655 0 0 1-1.64 0L3 12.43a1.93 1.93 0 0 1 0-3.36z"/>
    <path class="o o3" pathLength="100" d="M20 13v3.87a2.06 2.06 0 0 1-1.11 1.83l-6 3.08a1.93 1.93 0 0 1-1.78 0l-6-3.08A2.06 2.06 0 0 1 4 16.87V13"/>
    <path class="o o4" pathLength="100" d="M21 12.43a1.93 1.93 0 0 0 0-3.36L8.83 2.2a1.64 2 0 0 0-1.63 0L3 4.57a1.93 1.93 0 0 0 0 3.36l12.18 6.86a1.636 1.636 0 0 0 1.63 0z"/>
  </g>
</svg>

<style>
  .pkgAnim{
    width: var(--pa-size);
    height: var(--pa-size);
    --ease: cubic-bezier(.2,.9,.2,1);
  }

  .state{
    transform-origin: center;
    transition:
      opacity var(--pa-fade) var(--ease),
      transform var(--pa-fade) var(--ease);
    will-change: opacity, transform;
  }

  .closed{ opacity: 1; }
  .open{
    opacity: 0;
    transform: translateY(-0.025rem) scale(1.01);
  }

  .open .o{
    stroke-dasharray: 100;
    stroke-dashoffset: 100;
    transition: stroke-dashoffset var(--pa-draw) var(--ease);
    will-change: stroke-dashoffset;
  }

  .pkgAnim:is(:hover, .is-active) .closed{
    opacity: 0;
    transform: translateY(0.0312rem) scale(0.99);
  }

  .pkgAnim:is(:hover, .is-active) .open{
    opacity: 1;
    transform: translateY(0) scale(1);
  }

  .pkgAnim:is(:hover, .is-active) .open .o{
    stroke-dashoffset: 0;
  }

  .o1{ transition-delay: 0ms; }
  .o2{ transition-delay: 40ms; }
  .o3{ transition-delay: 90ms; }
  .o4{ transition-delay: 130ms; }

  @media (prefers-reduced-motion: reduce){
    .state, .open .o{ transition: none; }
    .pkgAnim:is(:hover, .is-active) .closed{ opacity: 0; transform: none; }
    .pkgAnim:is(:hover, .is-active) .open{ opacity: 1; transform: none; }
    .open .o{ stroke-dashoffset: 0; }
  }
</style>