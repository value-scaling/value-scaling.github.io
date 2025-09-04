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
      if (match) return { type: "mathBlock", raw: match[0], text: match[1].trim() };
    },
    renderer: (token: any) => `<div class="math math-block">${renderMath(token.text, true)}</div>`
  };

  const mathInline = {
    name: "mathInline",
    level: "inline",
    start: (src: string) => src.match(/\$/)?.index,
    tokenizer(src: string) {
      const match = /^\$([^\$\n]+?)\$/.exec(src);
      if (match) return { type: "mathInline", raw: match[0], text: match[1].trim() };
    },
    renderer: (token: any) => `<span class="math math-inline">${renderMath(token.text, false)}</span>`
  };

  const customRenderer = {
    link(href: string, title: string | null, text: string) {
      const isInternal = /^(\/|#|[A-Za-z0-9\-_]+(\.html?)?$)/.test(href);
      let out = `<a href="${encodeURI(href)}" class="link"`;
      if (!isInternal) out += ` target="_blank" rel="external noopener noreferrer"`;
      if (title) out += ` title="${title}"`;
      out += `>${text}</a>`;
      return out;
    },
    heading(text: string, level: number, raw: string, slugger: any) {
      const id = slugger ? slugger.slug(raw) : String(raw || text)
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
      // Keep plain heading text; the scroll meter will link to #id
      return `<h${level} id="${id}">${text}</h${level}>`;
    },
    blockquote(quote: string) {
      return `<blockquote class="inline-block bg-neutral-50 border-l-4 border-neutral-600 rounded px-3 py-2 align-middle my-2">${quote}</blockquote>`;
    }
  };

  const imageAttrExtension = {
    name: 'imageAttr',
    level: 'inline',
    start: (src: string) => src.indexOf('!['),
    tokenizer(src: string) {
      const re = /^!\[([^\]]*)\]\((\S+?)(?:\s+"([^"]*)")?\)\{([^}]+)\}/;
      const match = re.exec(src);
      if (match) {
        const [raw, alt, srcUrl, title, attrStr] = match;
        const attrs: Record<string, string> = {};
        attrStr.split(/\s+/).forEach(tok => {
          if (!tok) return;
          const eq = tok.indexOf('=');
          if (eq === -1) {
            attrs[tok] = '';
          } else {
            const k = tok.slice(0, eq);
            const v = tok.slice(eq + 1).replace(/^["']|["']$/g, '');
            if (k) attrs[k] = v;
          }
        });
        return { type: 'imageAttr', raw, alt, src: srcUrl, title, attrs };
      }
    },
    renderer(token: any) {
      const isVideoSrc = /\.(mp4|webm|ogg)(\?.*)?$/i.test(token.src);
      const declaresVideo = token.attrs['type'] === 'video' || Object.prototype.hasOwnProperty.call(token.attrs, 'video');
      if (isVideoSrc || declaresVideo) {
        const lower = token.src.toLowerCase();
        const sourceType =
          token.attrs['source-type'] ||
          (lower.endsWith('.webm') ? 'video/webm' : lower.endsWith('.ogg') ? 'video/ogg' : 'video/mp4');
        let out = `<video class="block mx-auto" aria-label="${token.alt || ''}"`;
        const hasControls = Object.prototype.hasOwnProperty.call(token.attrs, 'controls');
        const hasPlaysinline = Object.prototype.hasOwnProperty.call(token.attrs, 'playsinline');
        for (const k in token.attrs) {
          if (k === 'type' || k === 'video' || k === 'source-type') continue;
          const val = token.attrs[k];
          out += val === '' ? ` ${k}` : ` ${k}="${val}"`;
        }
        if (!hasControls) out += ' controls';
        if (!hasPlaysinline) out += ' playsinline';
        out += `><source src="${token.src}" type="${sourceType}" /></video>`;
        if (token.title) {
          out += `<p class='text-center text-gray-500 mb-4'>${token.title}</p>`;
        }
        return out;
      } else {
        let out = `<img src="${token.src}" alt="${token.alt}" class="block mx-auto"`;
        for (const k in token.attrs) {
          out += ` ${k}="${token.attrs[k]}"`;
        }
        out += ' />';
        if (token.title) {
          out += `<p class='text-center text-gray-500 mb-4'>${token.title}</p>`;
        }
        return out;
      }
    }
  };

  marked.use({
    gfm: true,
    extensions: [imageAttrExtension, mathBlock, mathInline],
    renderer: customRenderer
  });
</script>

<script lang="ts">
  import Jumpbox from "./Jumpbox.svelte";
  import TakeawayBox from './TakeawayBox.svelte';
  
  export let source: string;

  type Chunk =
    | { type: 'text'; content: string }
    | { type: 'jumpbox'; id: string; label: string }
    | { type: 'takeaway'; content: string };

  // Regexes (global + multiline). We scan by hand using lastIndex.
  const JUMP_RE = /:::jumpbox\s+id="([^"]+)"(?:\s+label="([^"]+)")?\s*:::/gm;
  const TAKE_BEGIN_RE = /:::takeaway_begin:::/gm;
  const TAKE_END_RE = /:::takeaway_end:::/gm;

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

      // No more markers → push rest as text and stop
      if (!j && !t) {
        if (pos < source.length) out.push({ type: 'text', content: source.slice(pos) });
        break;
      }

      // Choose the earliest marker by index
      const j_idx = j ? j.index : Infinity;
      const t_idx = t ? t.index : Infinity;

      if (j_idx <= t_idx) {
        // Emit pre-text
        if (j_idx > pos) out.push({ type: 'text', content: source.slice(pos, j_idx) });

        const id = j![1];
        const label = j![2] ?? id;
        out.push({ type: 'jumpbox', id, label });

        // Advance past this jumpbox
        pos = JUMP_RE.lastIndex;
      } else {
        // Takeaway begin comes first
        const begin_idx = t!.index;
        const begin_end = begin_idx + t![0].length;

        // Emit pre-text
        if (begin_idx > pos) out.push({ type: 'text', content: source.slice(pos, begin_idx) });

        // Find matching end after the begin
        TAKE_END_RE.lastIndex = begin_end;
        const tend = TAKE_END_RE.exec(source);

        if (!tend) {
          // No closing marker → treat the begin marker as plain text (no guessing)
          out.push({ type: 'text', content: source.slice(begin_idx, begin_end) });
          pos = begin_end;
          continue;
        }

        const inner_md = source.slice(begin_end, tend.index).trim();
        out.push({ type: 'takeaway', content: inner_md });

        // Advance past the end marker
        pos = TAKE_END_RE.lastIndex;
      }
    }

    return out;
  })();
</script>

<div class="md-output space-y-6">
  {#each chunks as chunk, i (i)}
    {#if chunk.type === 'text'}
      <div class="md-output">{@html toHtml(chunk.content)}</div>
    {:else if chunk.type === 'jumpbox'}
      <Jumpbox id={chunk.id} label={chunk.label} />
    {:else if chunk.type === 'takeaway'}
      <TakeawayBox html={toHtml(chunk.content)} />
    {/if}
  {/each}
</div>

<style lang="postcss">
  :global(.md-output h1) { @apply text-3xl font-bold mt-6 mb-4 }
  :global(.md-output h2) { @apply text-2xl font-semibold mt-5 mb-3 }
  :global(.md-output h3) { @apply text-xl font-semibold mt-4 mb-2 }
  :global(.md-output h4) { @apply text-lg font-semibold mt-3 mb-2 }

  :global(.md-output p) { @apply mb-4 }
  :global(.md-output strong) { @apply font-semibold }
  :global(.md-output em) { @apply italic }
  :global(.md-output code) { @apply text-[95%] bg-neutral-100 px-1 rounded }

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

  :global(.math-block) { @apply my-4 text-center }
  :global(.math-inline) { @apply align-baseline }
  :global(.katex-error) { @apply text-red-600 bg-red-100 p-1 rounded }
  :global(.md-output blockquote) { @apply inline-block align-middle bg-neutral-50 rounded px-3 py-2 my-2 border-l-4 border-neutral-600; }
  :global(.md-output blockquote > :first-child) { @apply mt-0; }
  :global(.md-output blockquote > :last-child) { @apply mb-0; }
</style>
