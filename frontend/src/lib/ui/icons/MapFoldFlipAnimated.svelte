<!-- MapFoldFlipAnimated.svelte -->
<script lang="ts">
  export let size: number = 24;       // px
  export let speed: number = 180;     // ms
  export let delta: number = 1;       // px (сдвиг граней вверх/вниз)
  export let active: boolean = false; // программный запуск как hover
  export let ariaLabel: string = 'Map';
  export let title: string | null = null;
  export let className: string = '';
</script>

<svg
  class={`mapFlip ${active ? 'is-active' : ''} ${className}`}
  style={`--mf-size:${size}px; --mf-speed:${speed}ms; --mf-delta:${delta}px;`}
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

  <!-- Edge 1 (left outer) + segments to edge 2 -->
  <g class="edge e1">
    <path d="M3 6.618V19.381" />
    <path class="seg s12 top" d="M3 6.618H9" />
    <path class="seg s12 bot" d="M3 19.381H9" />
  </g>

  <!-- Edge 2 (fold @ x=9) + segments to edge 3 -->
  <g class="edge e2">
    <path d="M9 3.236V18.236" />
    <path class="seg s23 top" d="M9 3.236H15" />
    <path class="seg s23 bot" d="M9 18.236H15" />
  </g>

  <!-- Edge 3 (fold @ x=15) + segments to edge 4 -->
  <g class="edge e3">
    <path d="M15 5.764V20.764" />
    <path class="seg s34 top" d="M15 5.764H21" />
    <path class="seg s34 bot" d="M15 20.764H21" />
  </g>

  <!-- Edge 4 (right outer) -->
  <g class="edge e4">
    <path d="M21 4.619V17.383" />
  </g>
</svg>

<style>
  .mapFlip{
    width: var(--mf-size);
    height: var(--mf-size);
    overflow: visible;
    --ease: cubic-bezier(.2,.9,.2,1);
  }

  .edge{
    transition: transform var(--mf-speed) var(--ease);
    will-change: transform;
  }

  /* 1 и 3 вверх, 2 и 4 вниз */
  .mapFlip:is(:hover, .is-active) .e1,
  .mapFlip:is(:hover, .is-active) .e3{
    transform: translateY(calc(-1 * var(--mf-delta)));
  }

  .mapFlip:is(:hover, .is-active) .e2,
  .mapFlip:is(:hover, .is-active) .e4{
    transform: translateY(var(--mf-delta));
  }

  /* соединяющие сегменты: skewY меняет угол */
  .seg{
    transform-box: fill-box;
    transform-origin: 0% 50%;
    transition: transform var(--mf-speed) var(--ease);
    will-change: transform;
  }

  /* Исходные углы */
  .s12.top{ transform: skewY(-29.4085deg); }
  .s23.top{ transform: skewY( 22.8473deg); }
  .s34.top{ transform: skewY(-10.8040deg); }

  .s12.bot{ transform: skewY(-10.8040deg); }
  .s23.bot{ transform: skewY( 22.8473deg); }
  .s34.bot{ transform: skewY(-29.4013deg); }

  /* Hover-углы (при delta=0.0625rem) */
  .mapFlip:is(:hover, .is-active) .s12.top{ transform: skewY(-12.9709deg); }
  .mapFlip:is(:hover, .is-active) .s23.top{ transform: skewY(  5.0291deg); }
  .mapFlip:is(:hover, .is-active) .s34.top{ transform: skewY(  8.1100deg); }

  .mapFlip:is(:hover, .is-active) .s12.bot{ transform: skewY(  8.1100deg); }
  .mapFlip:is(:hover, .is-active) .s23.bot{ transform: skewY(  5.0291deg); }
  .mapFlip:is(:hover, .is-active) .s34.bot{ transform: skewY(-12.9618deg); }

  @media (prefers-reduced-motion: reduce){
    .edge, .seg{ transition: none; }
    .mapFlip:is(:hover, .is-active) .e1,
    .mapFlip:is(:hover, .is-active) .e2,
    .mapFlip:is(:hover, .is-active) .e3,
    .mapFlip:is(:hover, .is-active) .e4{ transform: none; }
  }
</style>