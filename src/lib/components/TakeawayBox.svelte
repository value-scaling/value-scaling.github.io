<script lang="ts">
  export let html: string;  // already-marked HTML
</script>

<div class="my-4 rounded bg-slate-50 hover:bg-sky-50/50 p-4 pb-1 border-l-4 border-sky-700 transition">
  <div class="text-xs font-semibold tracking-wide uppercase text-sky-700">Takeaways</div>
  <div class="prose max-w-none mt-1">
    <div class="md-output">{@html html}</div>
  </div>
</div>
