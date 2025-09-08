<script context="module" lang="ts">
  import { marked } from "marked";
  import katex from "katex";
  import "katex/dist/katex.min.css";

  function renderMath(tex: string, displayMode: boolean) {
    try {
      return katex.renderToString(tex, { throwOnError: false, displayMode });
    } catch {
      const tag = displayMode ? "pre" : "code";
      return `<${tag} class="katex-error">${tex}</${tag}>`;
    }
  }

  const mathBlock = {
    name: "mathBlock",
    level: "block",
    start: (src: string) => src.match(/\$\$/)?.index,
    tokenizer(src: string) {
      const match = /^\$\$([\s\S]+?)\$\$/.exec(src);
      if (match)
        return { type: "mathBlock", raw: match[0], text: match[1].trim() };
    },
    renderer: (token: any) =>
      `<div class="math math-block">${renderMath(token.text, true)}</div>`,
  };

  const mathInline = {
    name: "mathInline",
    level: "inline",
    start: (src: string) => src.match(/\$/)?.index,
    tokenizer(src: string) {
      const match = /^\$([^\$\n]+?)\$/.exec(src);
      if (match)
        return { type: "mathInline", raw: match[0], text: match[1].trim() };
    },
    renderer: (token: any) =>
      `<span class="math math-inline">${renderMath(token.text, false)}</span>`,
  };

  const customRenderer = {
    link(href: string, title: string | null, text: string) {
      const isInternal = /^(\/|#|[A-Za-z0-9\-_]+(\.html?)?$)/.test(href);
      let out = `<a href="${encodeURI(href)}" class="link"`;
      if (!isInternal)
        out += ` target="_blank" rel="external noopener noreferrer"`;
      if (title) out += ` title="${title}"`;
      out += `>${text}</a>`;
      return out;
    },
    heading(text: string, level: number, raw: string, slugger: any) {
      const id = slugger
        ? slugger.slug(raw)
        : String(raw || text)
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
      // Keep plain heading text; the scroll meter will link to #id
      return `<h${level} id="${id}">${text}</h${level}>`;
    },
    blockquote(quote: string) {
      return `<blockquote class="inline-block bg-neutral-50 border-l-4 border-neutral-600 rounded px-3 py-2 align-middle my-2">${quote}</blockquote>`;
    },
  };

  const imageAttrExtension = {
    name: "imageAttr",
    level: "inline",
    start: (src: string) => src.indexOf("!["),
    tokenizer(src: string) {
      const re = /^!\[([^\]]*)\]\((\S+?)(?:\s+"([^"]*)")?\)\{([^}]+)\}/;
      const match = re.exec(src);
      if (match) {
        const [raw, alt, srcUrl, title, attrStr] = match;
        const attrs: Record<string, string> = {};
        attrStr.split(/\s+/).forEach((tok) => {
          if (!tok) return;
          const eq = tok.indexOf("=");
          if (eq === -1) {
            attrs[tok] = "";
          } else {
            const k = tok.slice(0, eq);
            const v = tok.slice(eq + 1).replace(/^["']|["']$/g, "");
            if (k) attrs[k] = v;
          }
        });
        return { type: "imageAttr", raw, alt, src: srcUrl, title, attrs };
      }
    },
    renderer(token: any) {
      const isVideoSrc = /\.(mp4|webm|ogg)(\?.*)?$/i.test(token.src);
      const declaresVideo =
        token.attrs["type"] === "video" ||
        Object.prototype.hasOwnProperty.call(token.attrs, "video");
      let out = "";
      if (isVideoSrc || declaresVideo) {
        const lower = token.src.toLowerCase();
        const sourceType =
          token.attrs["source-type"] ||
          (lower.endsWith(".webm")
            ? "video/webm"
            : lower.endsWith(".ogg")
              ? "video/ogg"
              : "video/mp4");

        // read optional freeze ms from markdown: {... freeze=10000}
        const freezeMs = token.attrs["freeze"] || "10000";

        out += `<video class="block mx-auto autoplay-on-fullview md-video" aria-label="${token.alt || ""}"`;
        const hasPlaysinline = Object.prototype.hasOwnProperty.call(
          token.attrs,
          "playsinline",
        );

        // forward arbitrary attrs except type/video/source-type/freeze/controls
        for (const k in token.attrs) {
          if (
            k === "type" ||
            k === "video" ||
            k === "source-type" ||
            k === "freeze" ||
            k === "controls"
          )
            continue;
          const val = token.attrs[k];
          out += val === "" ? ` ${k}` : ` ${k}="${val}"`;
        }

        // autoplay reliability
        out += " muted playsinline"; // keep muted for autoplay; playsinline for iOS
        if (!hasPlaysinline) out += " playsinline";

        // carry freeze config for runtime
        out += ` data-freeze-ms="${freezeMs}"`;

        // do NOT add controls here; we’ll toggle on hover via JS
        out += `><source src="${token.src}#t=0.1" type="${sourceType}" /></video>`;
      } else {
        out += `<img src="${token.src}" alt="${token.alt}" class="block mx-auto"`;
        for (const k in token.attrs) {
          out += ` ${k}="${token.attrs[k]}"`;
        }
        out += " />";
      }
      if (token.title) {
        out += `<div class='text-center text-gray-500 mb-4 md:px-8 lg:px-12 text-sm'>${marked.parse(token.title, { smartypants: true })}</div>`;
      }
      return out;
    },
  };

  marked.use({
    gfm: true,
    extensions: [imageAttrExtension, mathBlock, mathInline],
    renderer: customRenderer,
  });
</script>

<script lang="ts">
  import Jumpbox from "./Jumpbox.svelte";
  import TakeawayBox from "./TakeawayBox.svelte";

  export let source: string;

  type Chunk =
    | { type: "text"; content: string }
    | { type: "jumpbox"; id: string; label: string }
    | { type: "takeaway"; content: string }
    | { type: "small"; content: string };

  // Regexes (global + multiline). We scan by hand using lastIndex.
  const JUMP_RE = /:::jumpbox\s+id="([^"]+)"(?:\s+label="([^"]+)")?\s*:::/gm;
  const TAKE_BEGIN_RE = /:::takeaway_begin:::/gm;
  const TAKE_END_RE = /:::takeaway_end:::/gm;
  const SMALL_BEGIN_RE = /:::small_begin:::/gm;
  const SMALL_END_RE = /:::small_end:::/gm;

  function toHtml(md: string) {
    return marked.parse(md, { smartypants: true });
  }

  // One-pass tokenizer across the whole document
  $: chunks = (() => {
    const out: Chunk[] = [];
    let pos = 0;

    while (pos < source.length) {
      // Find next possible jumpbox or takeaway-begin after pos
      JUMP_RE.lastIndex = pos;
      TAKE_BEGIN_RE.lastIndex = pos;

      const j = JUMP_RE.exec(source);
      const t = TAKE_BEGIN_RE.exec(source);
      const s = SMALL_BEGIN_RE.exec(source);

      // No more markers → push rest as text and stop
      if (!j && !t && !s) {
        if (pos < source.length)
          out.push({ type: "text", content: source.slice(pos) });
        break;
      }

      // Choose the earliest marker by index
      const j_idx = j ? j.index : Infinity;
      const t_idx = t ? t.index : Infinity;
      const s_idx = s ? s.index : Infinity;

      if (j_idx <= t_idx && j_idx <= s_idx) {
        // Emit pre-text
        if (j_idx > pos)
          out.push({ type: "text", content: source.slice(pos, j_idx) });

        const id = j![1];
        const label = j![2] ?? id;
        out.push({ type: "jumpbox", id, label });

        // Advance past this jumpbox
        pos = JUMP_RE.lastIndex;
      } else if (t_idx <= j_idx && t_idx <= s_idx) {
        // Takeaway begin comes first
        const begin_idx = t!.index;
        const begin_end = begin_idx + t![0].length;

        // Emit pre-text
        if (begin_idx > pos)
          out.push({ type: "text", content: source.slice(pos, begin_idx) });

        // Find matching end after the begin
        TAKE_END_RE.lastIndex = begin_end;
        const tend = TAKE_END_RE.exec(source);

        if (!tend) {
          // No closing marker → treat the begin marker as plain text (no guessing)
          out.push({
            type: "text",
            content: source.slice(begin_idx, begin_end),
          });
          pos = begin_end;
          continue;
        }

        const inner_md = source.slice(begin_end, tend.index).trim();
        out.push({ type: "takeaway", content: inner_md });

        // Advance past the end marker
        pos = TAKE_END_RE.lastIndex;
      } else {
        // Small begin comes first
        const begin_idx = s!.index;
        const begin_end = begin_idx + s![0].length;

        // Emit pre-text
        if (begin_idx > pos)
          out.push({ type: "text", content: source.slice(pos, begin_idx) });

        // Find matching end after the begin
        SMALL_END_RE.lastIndex = begin_end;
        const send = SMALL_END_RE.exec(source);

        if (!send) {
          // No closing marker → treat the begin marker as plain text
          out.push({
            type: "text",
            content: source.slice(begin_idx, begin_end),
          });
          pos = begin_end;
          continue;
        }

        const inner_md = source.slice(begin_end, send.index).trim();
        out.push({ type: "small", content: inner_md });

        // Advance past the end marker
        pos = SMALL_END_RE.lastIndex;
      }
    }

    return out;
  })();

  import { onMount, afterUpdate, onDestroy } from "svelte";

  let container: HTMLDivElement | null = null;

  function setupVideos(root: HTMLElement) {
    const videos = Array.from(
      root.querySelectorAll<HTMLVideoElement>("video.autoplay-on-fullview"),
    );

    // De-dup if we re-run on updates
    const fresh = videos.filter((v) => !v.dataset._wired);

    if (fresh.length === 0) return;

    // Hover controls (desktop), keep hidden otherwise
    for (const v of fresh) {
      v.controls = false; // hidden by default
      v.dataset._wired = "1";

      let is_touch = false;
      const onFirstTouch = () => {
        is_touch = true;
        window.removeEventListener("touchstart", onFirstTouch);
      };
      window.addEventListener("touchstart", onFirstTouch, {
        passive: true,
        once: true,
      });

      const show = () => {
        if (!is_touch) v.controls = true;
      };
      const hide = () => {
        if (!is_touch) v.controls = false;
      };
      v.addEventListener("mouseenter", show);
      v.addEventListener("mouseleave", hide);
      v.addEventListener("focus", show);
      v.addEventListener("blur", hide);

      // Freeze at end → wait → restart
      let restart_timer: number | null = null;
      const clearTimer = () => {
        if (restart_timer !== null) {
          window.clearTimeout(restart_timer);
          restart_timer = null;
        }
      };

      const onEnded = () => {
        const freeze_ms = parseInt(v.dataset.freezeMs || "10000", 10);
        clearTimer();
        // Last frame remains visible when paused after 'ended'
        restart_timer = window.setTimeout(() => {
          try {
            v.currentTime = 0;
          } catch {}
          const p = v.play();
          if (p && typeof (p as any).catch === "function")
            (p as any).catch(() => {});
        }, freeze_ms);
      };

      const cancelers = ["play", "pause", "seeking", "emptied", "abort"].map(
        (evt) => v.addEventListener(evt, clearTimer),
      );
      v.addEventListener("ended", onEnded);

      // Store cleanup hooks
      (v as any)._cleanupVideo = () => {
        v.removeEventListener("mouseenter", show);
        v.removeEventListener("mouseleave", hide);
        v.removeEventListener("focus", show);
        v.removeEventListener("blur", hide);
        v.removeEventListener("ended", onEnded);
        clearTimer();
      };
    }

    // IntersectionObserver for full-visibility autoplay
    // Create once and stash it; reuse across updates.
    if (!(setupVideos as any)._io) {
      const io = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            const v = entry.target as HTMLVideoElement;
            // cancel pending restart if visibility changed
            const clear = (v as any)._clearRestartTimer as
              | (() => void)
              | undefined;
            if (clear) clear();

            if (entry.intersectionRatio >= 1.0) {
              const p = v.play();
              if (p && typeof (p as any).catch === "function")
                (p as any).catch(() => {});
            } else {
              v.pause();
            }
          }
        },
        { threshold: 1.0 },
      );

      (setupVideos as any)._io = io;
    }

    const io: IntersectionObserver = (setupVideos as any)._io;
    fresh.forEach((v) => io.observe(v));
  }

  onMount(() => {
    if (container) setupVideos(container);
  });

  afterUpdate(() => {
    if (container) setupVideos(container); // handle markdown re-render
  });

  onDestroy(() => {
    if (!(setupVideos as any)._io) return;
    const io: IntersectionObserver = (setupVideos as any)._io;
    if (!container) return;
    container.querySelectorAll("video.autoplay-on-fullview").forEach((v) => {
      io.unobserve(v);
      const cleanup = (v as any)._cleanupVideo;
      if (cleanup) cleanup();
    });
  });
</script>

<div class="md-output space-y-6" bind:this={container}>
  {#each chunks as chunk, i (i)}
    {#if chunk.type === "text"}
      <div class="md-output">{@html toHtml(chunk.content)}</div>
    {:else if chunk.type === "jumpbox"}
      <Jumpbox id={chunk.id} label={chunk.label} />
    {:else if chunk.type === "takeaway"}
      <TakeawayBox html={toHtml(chunk.content)} />
    {:else if chunk.type === "small"}
      <div class="md-output text-sm sm-block">{@html toHtml(chunk.content)}</div>
    {/if}
  {/each}
</div>

<style lang="postcss">
  :global(.md-output h1) {
    @apply text-3xl font-bold mt-6 mb-4;
  }
  :global(.md-output h2) {
    @apply text-2xl font-semibold mt-5 mb-3;
  }
  :global(.md-output h3) {
    @apply text-xl font-semibold mt-4 mb-2;
  }
  :global(.md-output h4) {
    @apply text-lg font-semibold mt-3 mb-2;
  }

  :global(.md-output p) {
    @apply mb-4;
  }
  :global(.md-output strong) {
    @apply font-semibold;
  }
  :global(.md-output em) {
    @apply italic;
  }
  :global(.md-output code) {
    @apply text-[95%] bg-neutral-100 px-1 rounded;
  }

  :global(.md-output pre) {
    @apply bg-neutral-100 p-4 rounded overflow-x-auto mb-4;
  }

  :global(.md-output ul) {
    @apply list-disc list-outside ml-5 pl-5 mb-4 space-y-1;
  }
  :global(.md-output ol) {
    @apply list-decimal list-outside ml-5 pl-5 mb-4 space-y-1;
  }

  :global(.md-output li) {
    @apply mb-1;
  }

  :global(.math-block) {
    @apply my-4 text-center;
  }
  :global(.math-inline) {
    @apply align-baseline;
  }
  :global(.katex-error) {
    @apply text-red-600 bg-red-100 p-1 rounded;
  }
  :global(.md-output blockquote) {
    @apply inline-block align-middle bg-neutral-50 rounded px-3 py-2 my-2 border-l-4 border-neutral-600;
  }
  :global(.md-output blockquote > :first-child) {
    @apply mt-0;
  }
  :global(.md-output blockquote > :last-child) {
    @apply mb-0;
  }
  /* Small-section overrides: drop each heading one step inside .sm-block */
  :global(.sm-block h1) { @apply text-2xl font-bold mt-6 mb-4; }
  :global(.sm-block h2) { @apply text-xl font-semibold mt-5 mb-3; }
  :global(.sm-block h3) { @apply text-lg font-semibold mt-4 mb-2; }
  :global(.sm-block h4) { @apply text-base font-semibold mt-3 mb-2; }
  /* Make inline code a touch smaller relative to the smaller text size */
  :global(.sm-block code) { @apply text-[90%]; }
  /* Optional: tighten paragraphs slightly in small blocks */
  /* :global(.sm-block p) { @apply mb-3; } */

</style>
