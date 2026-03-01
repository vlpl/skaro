<!-- LayoutGridAnimated.svelte -->
<script lang="ts">
  export let size: number = 24;   // px
  export let speed: number = 320; // ms на один квадрант
  export let active: boolean = false;

  // задержка между квадрантами
  $: step = Math.max(0, Math.round(speed * 0.28));
</script>

<svg
  class={`grid-spin ${active ? 'is-active' : ''}`}
  style={`--speed:${speed}ms; --step:${step}ms;`}
  xmlns="http://www.w3.org/2000/svg"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-label="Layout grid"
>
  <rect class="q q1" width="7" height="7" x="3"  y="3"  rx="1" />
  <rect class="q q2" width="7" height="7" x="14" y="3"  rx="1" />
  <rect class="q q3" width="7" height="7" x="14" y="14" rx="1" />
  <rect class="q q4" width="7" height="7" x="3"  y="14" rx="1" />
</svg>

<style>
  .grid-spin .q {
    transform-box: fill-box;
    transform-origin: center;
    will-change: transform;
  }

  .grid-spin:is(:hover, .is-active) .q {
    animation-name: spinPop;
    animation-duration: var(--speed);
    animation-timing-function: cubic-bezier(.2,.9,.2,1);
    animation-iteration-count: 1;
    animation-fill-mode: both;
  }

  .grid-spin:is(:hover, .is-active) .q1 { animation-delay: calc(var(--step) * 0); }
  .grid-spin:is(:hover, .is-active) .q2 { animation-delay: calc(var(--step) * 1); }
  .grid-spin:is(:hover, .is-active) .q3 { animation-delay: calc(var(--step) * 2); }
  .grid-spin:is(:hover, .is-active) .q4 { animation-delay: calc(var(--step) * 3); }

  @keyframes spinPop {
    0%   { transform: rotate(0deg)   scale(1); }
    35%  { transform: rotate(140deg) scale(1.12); }
    70%  { transform: rotate(300deg) scale(0.98); }
    100% { transform: rotate(360deg) scale(1); }
  }

  @media (prefers-reduced-motion: reduce) {
    .grid-spin:is(:hover, .is-active) .q { animation: none; }
  }
</style>
