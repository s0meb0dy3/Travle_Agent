<template>
  <section class="glass-card rounded-[2rem] p-6">
    <div class="flex items-center justify-between gap-4">
      <div>
        <p class="section-label">Tips</p>
        <p class="font-display mt-4 text-3xl font-bold">出发前提醒</p>
      </div>
      <div class="rounded-full bg-[rgba(28,167,236,0.12)] px-4 py-2 text-sm font-medium text-[var(--sky)]">
        少踩坑
      </div>
    </div>

    <div class="mt-6 grid gap-3">
      <article
        v-for="(tip, index) in tips"
        :key="tip"
        class="rounded-[1.5rem] bg-white/80 p-4"
      >
        <p class="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Tip {{ index + 1 }}</p>
        <p class="mt-3 text-sm leading-6 text-[var(--text)]">{{ tip }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  tips: readonly string[];
}>();
</script>
