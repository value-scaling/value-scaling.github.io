<script lang="ts">
  import Star from "lucide-svelte/icons/star";
  import Markdown from "$lib/components/Markdown.svelte";
  import { formatTime } from "$lib/utils";

  type Resource = { label: string; url: string };
  type Project = {
    title: string;
    date: string;
    link: string;
    content: string;
    repo: string;
    topics: string[];
    lead: string;
    image_before: string;
    image_after: string;
    image_border?: boolean;
    subimages?: string[];
    highlight: boolean;
    resources?: Resource[];           // ← new!
  };

  export let data: Project;
  export let stars: Record<string, number> | null = null;

  let hovered = false;
  $: image_path = hovered ? data.image_after : data.image_before;
</script>

<div
  role="group"
  class="block -mx-4 mb-4 px-4 py-4 transition-colors
    {data.highlight ? 'hover:bg-sky-50 bg-sky-50' : ''}
  "
  on:mouseenter={() => (hovered = true)}
  on:mouseleave={() => (hovered = false)}
>
  <div class="grid grid-cols-4 gap-4">
    <!-- image & title as before… -->
    <div class="col-span-4 md:col-span-1">
      <img
        src="{image_path}"
        alt="{data.title} preview image"
        class:border={data.image_border}
        class="w-full max-w-40 mx-auto"
      />
    </div>
    <div class="col-span-4 md:col-span-3">
      <h3 class="text-black text-lg font-semibold mb-2">
        <a class="link-no-underline mr-1" href={data.link} target="_blank">
          {data.title}
        </a>
        <small class="whitespace-nowrap text-neutral-500 text-base font-normal">
          {formatTime("%B %Y", data.date)}
        </small>
      </h3>
      <div class="text-sm reduced-spacing">
        <Markdown source={data.content} />
      </div>

      {#if data.resources?.length}
        <div class="flex flex-wrap gap-2">
          {#each data.resources as { label, url }}
            <a
              href={url}
              target="_blank"
              class="px-2 py-1 bg-sky-700 text-white text-[0.9rem] leading-[1rem] rounded hover:bg-sky-800 transition"
            >
              {label}
            </a>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  {#if data.subimages}
    <div class="grid grid-cols-3 gap-4 md:gap-8 lg:gap-12 mt-4">
      {#each data.subimages as img}
        <div class="col-span-full md:col-span-1">
          <img src="{img}" alt="{data.title} subimage"/>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style lang="postcss">
  .pill {
    @apply flex items-center text-sm font-medium px-1.5 py-[1px] mr-1.5 mb-2
           bg-neutral-100 rounded-full;
  }

  :global(.reduced-spacing p) {
    @apply mb-2;
  }
</style>
