<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';

  /** The element whose scroll progress we track (e.g. "#article .md-output") */
  export let containerSelector = '.md-output';
  /** Which headings become ticks */
  export let headingsSelector = 'h2, h3';

  type Heading = { id: string; level: 2 | 3; top: number; label: string };

  let headings: Heading[] = [];
  let progress = 0;            // 0..1, revealed portion of the gradient (top -> bottom)
  let active_index = -1;
  let container_el: HTMLElement | null = null;
  let ready = false;
  let raf_id: number;
  let hydrated = false;

  function doc_y(el: Element) {
    const r = el.getBoundingClientRect();
    return (browser ? window.scrollY : 0) + r.top;
  }

  function should_include_heading(h: HTMLElement) {
    if (h.hasAttribute('data-skip-meter')) return false;
    if (h.getAttribute('data-meter') === 'false') return false;
    if (h.classList.contains('no-meter')) return false;
    return true;
  }

  function recompute() {
    if (!browser) return;
    container_el = document.querySelector(containerSelector) as HTMLElement | null;

    const nodes = container_el
      ? container_el.querySelectorAll(headingsSelector)
      : document.querySelectorAll(headingsSelector);

    headings = Array.from(nodes)
      .filter((el) => should_include_heading(el as HTMLElement))
      .map((el) => {
        const h = el as HTMLElement;
        if (!h.id) {
          // Fallback: generate a readable id from text content
          h.id = (h.textContent || '')
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
        }
        return {
          id: h.id,
          level: h.tagName === 'H2' ? 2 : 3,
          top: doc_y(h),
          label: (h.textContent || '').trim()
        };
      });

    update_progress();
  }

  function update_progress() {
    if (!browser) return;

    // Use the viewport center line for progress
    // Progress should start at 0 when the container's TOP reaches the viewport TOP
    const yTop = window.scrollY;
    if (!container_el) {
      // Fallback to whole document with center-line semantics
      // Fallback: whole document, top-of-viewport semantics
      const start = 0;
      const denom = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
      progress = Math.min(1, Math.max(0, (yTop - start) / denom));
    } else {
      const start = doc_y(container_el);                                            // empty when container top hits viewport top
      const denom = Math.max(container_el.getBoundingClientRect().height - window.innerHeight, 1);
      progress = Math.min(1, Math.max(0, (yTop - start) / denom));
    }

    // Active tick: last heading that passed the top of the viewport (small offset for stability)
    const y = window.scrollY + 8;
    let idx = -1;
    for (let i = 0; i < headings.length; i++) {
      if (headings[i].top <= y) idx = i;
      else break;
    }
    active_index = idx;
  }

  function tick_frac(h: Heading) {
    if (!container_el) {
      const doc = document.documentElement;
      const denom = Math.max(doc.scrollHeight - 0, 1);
      return Math.min(1, Math.max(0, h.top / denom));
    }
    const start = doc_y(container_el);
    const height = container_el.getBoundingClientRect().height;
    const end = start + height;
    return Math.min(1, Math.max(0, (h.top - start) / Math.max(end - start, 1)));
  }

  let onScroll: () => void;
  let onResize: () => void;
  let ro: ResizeObserver | null = null;

  onMount(() => {
    hydrated = true;
    raf_id = requestAnimationFrame(() => {
      recompute();
      update_progress();
      ready = true;
    });
    onScroll = () => update_progress();
    onResize = () => recompute();

    if (browser) {
      window.addEventListener('scroll', onScroll, { passive: true });
      window.addEventListener('resize', onResize);

      if (containerSelector) {
        const c = document.querySelector(containerSelector);
        if (c) {
          ro = new ResizeObserver(() => recompute());
          ro.observe(c);
        }
      }
    }
  });

  onDestroy(() => {
    if (browser) {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
    }
    if (ro) ro.disconnect();
    if (raf_id) cancelAnimationFrame(raf_id);
  });
</script>

<!--
  Fixed, full-height bar on the extreme left (fills viewport regardless of layout).
  The gradient is fixed over the full bar; we reveal it via clip-path based on `progress`.
  Ticks are horizontal lines that start at the very left edge and extend into the page,
  and on hover they show the heading label to the right.
-->
<div class="scroll-meter" aria-hidden="true" class:ready={ready}>
  <div class="track">
    <div
      class="gradient"
      style={hydrated ? `clip-path: inset(0 0 ${100 - progress * 100}% 0);` : ''}
    ></div>

    {#if hydrated}
      {#each headings as h, i}
        <a
          href={`#${h.id}`}
          class={`tick ${i === active_index ? 'active' : ''} ${h.level === 3 ? 'sub' : ''}`}
          style={`top: calc(${tick_frac(h) * 100}% - 1px);`}
          aria-label={h.label}
          data-label={h.label}
        />
      {/each}
    {/if}
  </div>
</div>

<style>
  :root {
    --meter-width: 14px;   /* width of the vertical bar on the far left */
    --tick-length: 22px;   /* ticks extend into the page beyond the bar */
    --tick-length-sub: 18px;   /* ticks extend into the page beyond the bar */
    --tick-hitbox: 18px;
    --tick-line: 2px;
    --tick-color: #9ca3af; /* neutral-400 */
    --tick-color-sub: #c5cbd3;
    --tick-color-active: #111827; /* neutral-900 */
  }

  .scroll-meter {
    position: fixed;
    left: 0;          /* flush to the left edge of the screen */
    top: 0;           /* full height, regardless of layout */
    bottom: 0;
    width: var(--meter-width);
    pointer-events: none; /* let clicks pass through EXCEPT on ticks */
    z-index: 50;
    opacity: 0;
    transition: opacity 1000ms ease;
  }

  .scroll-meter.ready {
    opacity: 1;
  }

  .track {
    position: absolute;
    inset: 0;              /* fill the bar */
    background: white;     /* base is white; no edge/shadow */
    overflow: visible;     /* allow ticks to extend past the track */
  }

  /* Full-height fixed gradient (blue -> green).
     We reveal it by clipping the bottom by (1 - progress). */
  .gradient {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, #77aabb 0%, #bbcc33 100%); /* blue→green */
    will-change: clip-path;
  }

  /* Ticks: horizontal bars that begin at the left edge of the screen and extend into the page */
  .tick {
    position: absolute;
    left: 0;                          /* start at very left of the screen */
    width: var(--tick-length);        /* extend beyond bar width */
    height: var(--tick-hitbox);       /* bigger hitbox, invisible */
    background: transparent;          /* keep visible line separate */
    /* height: 2px; */
    /* background: var(--tick-color); */
    transform: translateY(-1px);
    pointer-events: auto;             /* clickable despite container being none */
    text-decoration: none;
    z-index: 2;                       /* above gradient */
    display: block;
    opacity: 0.9;
    transition: opacity 120ms ease;
  }

  /* visible 2px line centered within the larger hitbox (tick looks unchanged) */
  .tick::before {
    content: '';
    position: absolute;
    left: 0;
    width: var(--tick-length);
    height: var(--tick-line);         /* 2px visual line */
    top: 50%;
    transform: translateY(-50%);
    background: #595959;              /* neutral-400 */
  }

  .tick::before::hover {
    background: neutral-900;
  }

  .tick:hover {
    opacity: 1;
  }

  @media (max-width: 1439px) {
    .tick::after {
      display: none !important;
    }
  }

  .tick.sub::before {
    width: calc(var(--tick-length-sub));
    background: #868686; /* lighter gray */
  }

  .tick.sub::before::hover {
    background: neutral-900;
  }

  /* Active tick (closest passed heading at viewport center) */
  /* .tick.active::before {
    background: #111827; /* neutral-900 */
    /* height: 3px;
  } */

  /* Hover label: no bubble, bigger font; remove default HTML tooltip by not using title attr */
  /* .tick::after {
    content: attr(aria-label);
    position: absolute;
    left: calc(var(--tick-length) + 8px);
    top: 50%;
    transform: translateY(-50%);
    white-space: nowrap;
    font-size: 14px;
    line-height: 1.1;
    color: #111827;
    opacity: 0;
    transition: opacity 120ms ease;
    pointer-events: none;
  } */

  /* Tick labels on hover: fade in to the right of the tick */
  .tick::after {
    content: attr(data-label);
    position: absolute;
    left: calc(100% + 8px); /* to the right of the tick */
    top: 50%;
    transform: translateY(-50%);
    /* white-space: nowrap; */
    /* font-size: 18px; */
    width: var(--meter-gutter, 220px);
    white-space: normal;
    overflow-wrap: anywhere;
    font-size: 18px;
    line-height: 1.2;
    /* line-height: 1; */
    color: #374151; /* neutral-700 */
    /* background: rgba(255, 255, 255, 0.96); */
    padding: 2px 6px;
    /* border-radius: 6px; */
    /* box-shadow: 0 1px 2px rgba(0,0,0,0.08); */
    opacity: 0;
    pointer-events: none;
    transition: opacity 120ms ease;
  }

  .tick:hover::after {
    opacity: 1;
  }

  @media (max-width: 1024px) {
    .scroll-meter {
      display: none; /* hide on small screens */
    }
  }
</style>
