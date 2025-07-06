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

  const linkRenderer = {
    link(href: string, title: string | null, text: string) {
      const isInternal = /^(\/|#|[A-Za-z0-9\-_]+(\.html?)?$)/.test(href);
      let out = `<a href="${encodeURI(href)}" class="link"`;
      if (!isInternal) out += ` target="_blank" rel="external noopener noreferrer"`;
      if (title) out += ` title="${title}"`;
      out += `>${text}</a>`;
      return out;
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
        attrStr.split(/\s+/).forEach(pair => {
          const [k, v] = pair.split('=');
          if (k && v) attrs[k] = v.replace(/^["']|["']$/g, '');
        });
        return { type: 'imageAttr', raw, alt, src: srcUrl, title, attrs };
      }
    },
    renderer(token: any) {
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
  };

  marked.use({
    gfm: true,
    extensions: [imageAttrExtension, mathBlock, mathInline],
    renderer: linkRenderer
  });
</script>

<script lang="ts">
  import Jumpbox from "./Jumpbox.svelte";

  export let source: string;

  const JUMP_RE = /^:::jumpbox\s+id="([^"]+)"(?:\s+label="([^"]+)")?\s*:::/m;

  type Chunk = { type: "text"; content: string } | { type: "jumpbox"; id: string; label: string };

  $: chunks = (() => {
    const out: Chunk[] = [];
    let rest = source;
    let match: RegExpExecArray | null;

    while ((match = JUMP_RE.exec(rest))) {
      const [raw, id, label] = match;
      const idx = match.index;

      if (idx > 0) {
        out.push({ type: "text", content: rest.slice(0, idx) });
      }

      out.push({ type: "jumpbox", id, label: label ?? id });
      rest = rest.slice(idx + raw.length);
    }

    if (rest) out.push({ type: "text", content: rest });
    return out;
  })();

  function toHtml(md: string) {
    return marked.parse(md, { smartypants: true });
  }
</script>

<div class="md-output space-y-6">
  {#each chunks as chunk (chunk)}
    {#if chunk.type === "text"}
      <div>{@html toHtml(chunk.content)}</div>
    {:else}
      <Jumpbox id={chunk.id} label={chunk.label} />
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
</style>
