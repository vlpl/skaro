<script lang="ts">
  export let size: number = 24;
  export let active: boolean = false;
</script>

<svg
  class={`sparkles ${active ? 'is-active' : ''}`}
  style={`--sp-size:${size}px;`}
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
  aria-label="Features"
>
  <path class="main" d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
  <path class="s1" d="M5 3v4" />
  <path class="s2" d="M19 17v4" />
  <path class="s3" d="M3 5h4" />
  <path class="s4" d="M17 19h4" />
</svg>

<style>
  .sparkles {
    width: var(--sp-size);
    height: var(--sp-size);
    overflow: visible;
  }
  .main, .s1, .s2, .s3, .s4 {
    transition: transform 200ms cubic-bezier(.2,.9,.2,1);
    will-change: transform;
    transform-origin: center;
  }
  .s1, .s3 { transform-origin: 5px 5px; }
  .s2, .s4 { transform-origin: 19px 19px; }
  .sparkles:is(:hover, .is-active) .main { transform: scale(1.06) rotate(5deg); }
  .sparkles:is(:hover, .is-active) .s1 { transform: translateY(-1px); }
  .sparkles:is(:hover, .is-active) .s2 { transform: translateY(1px); }
  .sparkles:is(:hover, .is-active) .s3 { transform: translateX(-1px); }
  .sparkles:is(:hover, .is-active) .s4 { transform: translateX(1px); }

  @media (prefers-reduced-motion: reduce) {
    .main, .s1, .s2, .s3, .s4 { transition: none; }
  }
</style>
