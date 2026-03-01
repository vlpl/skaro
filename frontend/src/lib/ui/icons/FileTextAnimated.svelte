<!-- FileTextAnimated.svelte -->
<script lang="ts">
  export let size: number = 24;     // px
  export let speed: number = 320;   // ms (база)
  export let active: boolean = false; // можно дергать программно, как "hover"
  export let ariaLabel: string = 'File text';
  export let title: string | null = null;
  export let className: string = '';
</script>

<svg
  class={`fileText ${active ? 'is-active' : ''} ${className}`}
  style={`--ft-size:${size}px; --ft-speed:${speed}ms;`}
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

  <g class="doc">
    <!-- folded outline (со срезом угла) -->
    <path
      class="paper folded"
      d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"
    />

    <!-- flat outline (без среза) -->
    <path
      class="paper flat"
      d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2z"
    />

    <!-- внутренняя линия сгиба -->
    <path class="fold" d="M14 2v5a1 1 0 0 0 1 1h5" />

    <!-- дорисовка "разгиба" верх+право со скруглением (r=2) -->
    <path class="corner" pathLength="100" d="M14 2H18A2 2 0 0 1 20 4V8" />

    <!-- линии текста (видны ДО hover) -->
    <path class="line base" d="M10 9H8" />
    <path class="line base" d="M16 13H8" />
    <path class="line base" d="M16 17H8" />

    <!-- линии текста (оверлей-рост) -->
    <path class="line anim a1" pathLength="100" d="M10 9H8" />
    <path class="line anim a2" pathLength="100" d="M16 13H8" />
    <path class="line anim a3" pathLength="100" d="M16 17H8" />
  </g>
</svg>

<style>
  .fileText{
    width: var(--ft-size);
    height: var(--ft-size);

    --ease: cubic-bezier(.2,.9,.2,1);

    /* угол */
    --corner-delay: calc(var(--ft-speed) * 0.25);
    --corner-dur:   calc(var(--ft-speed) * 0.75);

    /* линии: в 2 раза медленнее */
    --line-step:  calc(var(--ft-speed) * 0.18);
    --line-dur:   calc(var(--ft-speed) * 1.70);
    --line-start: 70ms;
  }

  .fileText path,
  .fileText g{
    transform-box: fill-box;
    will-change: transform, opacity, stroke-dashoffset;
  }

  /* физичный "разгиб" */
  .doc{ transform-origin: center; }

  .fileText:is(:hover, .is-active) .doc{
    animation: docPop var(--ft-speed) var(--ease) 1 both;
  }

  @keyframes docPop{
    0%   { transform: translate(0,0) scale(1); }
    55%  { transform: translate(0,-0.0344rem) scale(1.02); }
    100% { transform: translate(0,-0.0156rem) scale(1.01); }
  }

  /* ключевое: убираем "срез" угла переключением обводки */
  .paper.folded{ opacity: 1; }
  .paper.flat{ opacity: 0; }

  .fileText:is(:hover, .is-active) .paper.folded{ opacity: 0; }
  .fileText:is(:hover, .is-active) .paper.flat{ opacity: 1; }

  /* сгиб: просто убрать на hover */
  .fileText:is(:hover, .is-active) .fold{ display: none; }

  /* дорисовка верх+право */
  .corner{
    opacity: 0;
    stroke-dasharray: 100;
    stroke-dashoffset: 100;
    stroke-linecap: round;
  }

  .fileText:is(:hover, .is-active) .corner{
    opacity: 1;
    animation: cornerDraw var(--corner-dur) var(--ease) 1 both;
    animation-delay: var(--corner-delay);
  }

  @keyframes cornerDraw{
    from { stroke-dashoffset: 100; }
    to   { stroke-dashoffset: 0; }
  }

  /* линии текста */
  .line.base{
    opacity: 1;
    transition: opacity 60ms ease;
  }

  .fileText:is(:hover, .is-active) .line.base{
    opacity: 0;
  }

  .line.anim{
    opacity: 0;
    stroke-dasharray: 100;
    stroke-dashoffset: 100;
  }

  .fileText:is(:hover, .is-active) .line.anim{
    animation: lineGrow var(--line-dur) var(--ease) 1 both;
  }

  .fileText:is(:hover, .is-active) .a1{ animation-delay: calc(var(--line-start) + var(--line-step) * 0); }
  .fileText:is(:hover, .is-active) .a2{ animation-delay: calc(var(--line-start) + var(--line-step) * 1); }
  .fileText:is(:hover, .is-active) .a3{ animation-delay: calc(var(--line-start) + var(--line-step) * 2); }

  @keyframes lineGrow{
    0%   { opacity: 0; stroke-dashoffset: 100; }
    8%   { opacity: 1; }
    100% { opacity: 1; stroke-dashoffset: 0; }
  }

  @media (prefers-reduced-motion: reduce){
    .fileText:is(:hover, .is-active) .doc{ animation: none; }
    .fileText:is(:hover, .is-active) .corner{ animation: none; }
    .fileText:is(:hover, .is-active) .line.anim{ animation: none; }

    /* без анимаций оставляем исходный вид */
    .paper.folded{ opacity: 1; }
    .paper.flat{ opacity: 0; }
    .fold{ display: inline; }
    .line.base{ opacity: 1; }
    .line.anim{ opacity: 0; }
    .corner{ opacity: 0; stroke-dashoffset: 100; }
  }
</style>