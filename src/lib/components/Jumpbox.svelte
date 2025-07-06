<script lang="ts">
  import { trimName } from '$lib/utils';

  // 1) Glob‐import all your project .md files (eager so we can sync extract titles)
  const projects = import.meta.glob('../../projects/*.md', { eager: true }) as Record<
    string,
    { title: string }
  >;

  // 2) Build an id→title map once
  const titleMap: Record<string, string> = Object.entries(projects).reduce(
    (acc, [path, mod]) => {
      const id = trimName(path) || path;
      acc[id] = mod.title;
      return acc;
    },
    {} as Record<string, string>
  );

  // 3) component API
  export let id: string;

  // 4) fallback to showing the raw id if no title found
  const label = titleMap[id] ?? id;
</script>

<a
  href={'#' + id}
  class="block -mx-4 mb-4 px-4 py-2 bg-gray-100 hover:bg-slate-100 rounded transition"
>
  <span class="text-neutral-500">↪</span> Our paper: <em>{label}</em>
</a>
