<!-- LayersAnimated.svelte -->
<script lang="ts">
  export let size: number = 24;       // px
  export let speed: number = 180;     // ms
  export let spread: number = 1.25;   // px (разъезд вверх/вниз)
  export let active: boolean = false; // можно включать программно
  export let ariaLabel: string = 'Layers';
  export let title: string | null = null;
  export let className: string = '';
</script>

<svg
  class={`layersIco ${active ? 'is-active' : ''} ${className}`}
  style={`--li-size:${size}px; --li-speed:${speed}ms; --li-spread:${spread}px;`}
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

  <path
    class="layer top"
    d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"
  />
  <path
    class="layer mid"
    d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"
  />
  <path
    class="layer bottom"
    d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"
  />
</svg>

<style>
  .layersIco{
    width: var(--li-size);
    height: var(--li-size);
    overflow: visible;
  }

  .layer{
    transform-box: fill-box;
    transform-origin: center;
    will-change: transform;
    transition: transform var(--li-speed) cubic-bezier(.2,.9,.2,1);
  }

  .layersIco:is(:hover, .is-active) .top{
    transform: translateY(calc(-1 * var(--li-spread)));
  }

  .layersIco:is(:hover, .is-active) .bottom{
    transform: translateY(var(--li-spread));
  }

  @media (prefers-reduced-motion: reduce){
    .layer{ transition: none; }
    .layersIco:is(:hover, .is-active) .top,
    .layersIco:is(:hover, .is-active) .bottom{ transform: none; }
  }
</style>