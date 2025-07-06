<script lang="ts">
  import ArrowUpRight from "lucide-svelte/icons/arrow-up-right";
  import Seo from "$lib/components/Seo.svelte";
  import Markdown from "$lib/components/Markdown.svelte";
  import Jumpbox from "$lib/components/Jumpbox.svelte";

  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import CalendarDays from "lucide-svelte/icons/calendar-days";
  import Star from "lucide-svelte/icons/star";

  import Project from "./projects/Project.svelte";
  import { trimName } from "$lib/utils";
  
  const projects = import.meta.glob("../projects/*.md", {
    eager: true,
  }) as any;

  $: projectsByDate = Object.keys(projects).sort(
    (a, b) => projects[b].date - projects[a].date
  );
  $: projectsByTitle = Object.keys(projects).sort((a, b) => {
    const titleA = projects[a].title.toLowerCase();
    const titleB = projects[b].title.toLowerCase();
    return titleA < titleB ? -1 : titleA > titleB ? 1 : 0;
  });

  onMount(() => {
    // Hack: Fix the scroll position after the page loads, especially for mobile browsers.
    const selected = $page.url.hash.slice(1);
    if (selected) {
      setTimeout(() => {
        if ($page.url.hash.slice(1) === selected) {
          document.getElementById(selected)?.scrollIntoView();
        }
      }, 500);
    }
  });

  let stars: Record<string, number> | null = null;
  onMount(async () => {
    const resp = await fetch(
      "https://api.github.com/users/ekzhang/repos?per_page=100"
    );
    const repos = await resp.json();
    stars = {};
    for (const obj of repos) {
      stars[obj.full_name] = obj.stargazers_count;
    }
  });

  $: projectsByStars = [...projectsByTitle].sort((a, b) => {
    const starsA = stars?.[projects[a].repo] ?? 0;
    const starsB = stars?.[projects[b].repo] ?? 0;
    return starsB - starsA;
  });

  let sortOrder: "date" | "stars" = "date";

  import maintext from '../maintext/main.md?raw';

</script>

<Seo title="Value-Based RL Scales" description="A project by UC Berkeley, CMU, and friends." />

<div class="layout-md text-lg space-y-12">
  <div class="space-y-2">
  {#each sortOrder === "date" ? projectsByDate : projectsByStars as id (id)}
    <section id={trimName(id)}>
      <!-- <div class="mx-auto max-w-[1152px] px-4 sm:px-6"> -->
        <Project data={projects[id]} {stars} />
      <!-- </div> -->
    </section>
  {/each}
  </div>
</div>

<div class="layout-md text-lg space-y-12">
  <Markdown source={maintext} />
</div>

<style lang="postcss">
  .g {
    @apply text-neutral-400;
  }

  em {
    @apply font-serif text-[110%] leading-[100%];
  }

  .project-pair {
    @apply grid sm:grid-cols-[1fr,2fr] gap-y-1 -mx-3 px-3 py-2 hover:bg-neutral-100 transition-colors;
  }

  aside {
    @apply mt-0.5 text-base text-neutral-500;
  }

  /* Correction for vertical navigation links on mobile. */
  @media (max-width: 420px) {
    #preston-is {
      @apply -mt-10;
    }
  }
</style>
