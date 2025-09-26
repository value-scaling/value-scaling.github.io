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
  // Treat image_after as an MP4 if it ends with .mp4; otherwise fall back to image hover swap.
  let is_video: boolean;
  $: is_video = /\.mp4($|\?)/.test(data.image_after ?? "");
  $: image_path = is_video
    ? `${data.image_before}`
    : hovered
      ? `${data.image_after}`
      : `${data.image_before}`;

  let video_el: HTMLVideoElement | null = null;

  const DEBUG = false;
  const log = (...args: any[]) => { if (DEBUG) console.log("[hover-video]", ...args); };
  let detach_listeners: Array<() => void> = [];
  function attachDebug(v: HTMLVideoElement) {
    // Log key media events and states
    const events = ["loadedmetadata","canplay","canplaythrough","play","pause","waiting","stalled","suspend","error","ended","timeupdate"];
    events.forEach((type) => {
      const h = (e: Event) => log(type, { readyState: v.readyState, networkState: v.networkState, currentTime: v.currentTime, paused: v.paused });
      v.addEventListener(type, h);
      detach_listeners.push(() => v.removeEventListener(type, h));
    });
    log("bound video", { src: data.image_after, canPlayType: v.canPlayType("video/mp4") });
    if (v.error) log("initial mediaError", v.error);
  }
</script>

<div
  role="group"
  class="block -mx-4 mb-4 px-4 py-4 transition-colors
    {data.highlight ? 'hover:bg-sky-50 bg-sky-50' : ''}
  "
  on:mouseenter={() => {
    hovered = true;
    if (!is_video || !video_el) return;
    // if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    //   log("skipping play due to prefers-reduced-motion");
    //   return;
    // }
    video_el.muted = true;
    video_el.playsInline = true;
    const p = video_el.play();
    log("play() called", { readyState: video_el.readyState, networkState: video_el.networkState });
    p.then(() => log("play() resolved")).catch((err) => log("play() rejected", err?.name, err?.message));
  }}
  on:mouseleave={() => {
    hovered = false;
    if (is_video && video_el) {
      video_el.pause();
      try { video_el.currentTime = 0; } catch {}
    }
  }}
>
  <div class="grid grid-cols-4 gap-4">
    <!-- image & title as before… -->
    <div class="col-span-4 md:col-span-1 unselectable">
      <div class="relative w-full max-w-80 mx-auto">
        <img
          src="{image_path}"
          alt="{data.title} preview image"
            class:border={data.image_border}
            class="w-full block"
          />
        {#if is_video}
          <video
            bind:this={video_el}
            class="absolute inset-0 w-full h-full object-cover pointer-events-none"
            style="opacity: {hovered ? 1 : 0}; transition: opacity 160ms ease;"
            preload="metadata"
            muted
            loop
            playsinline
            aria-hidden="true"
            tabindex="-1"
            poster="{data.image_before}"
          >
            <source src="{data.image_after}" type="video/mp4" />
          </video>
        {/if}
      </div>
    </div>
    <div class="col-span-4 md:col-span-3">
      <h3 class="text-black text-lg font-semibold mb-2 no-meter">
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
              class="px-2 py-1 bg-sky-700 text-white text-[0.9rem] leading-[1rem] rounded hover:bg-sky-800 transition unselectable"
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
