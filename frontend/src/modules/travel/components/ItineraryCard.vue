<template>
  <article class="glass-card rounded-[2rem] p-6 transition hover:translate-y-[-2px]">
    <div class="flex items-center justify-between gap-4">
      <div>
        <p class="font-display text-2xl font-bold">Day {{ day.day }}</p>
        <p class="mt-1 text-lg font-medium text-[var(--text)]">{{ day.title }}</p>
      </div>
      <div class="rounded-full bg-[rgba(242,92,42,0.12)] px-4 py-2 text-sm font-medium text-[var(--brand-strong)]">
        精简但可执行
      </div>
    </div>

    <div class="mt-6 grid gap-4 md:grid-cols-3">
      <section class="rounded-[1.5rem] bg-white/80 p-4">
        <p class="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Morning</p>
        <p class="mt-3 text-sm leading-6 text-[var(--text)]">{{ day.morning || "自由安排" }}</p>
      </section>
      <section class="rounded-[1.5rem] bg-white/80 p-4">
        <p class="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Afternoon</p>
        <p class="mt-3 text-sm leading-6 text-[var(--text)]">{{ day.afternoon || "自由安排" }}</p>
      </section>
      <section class="rounded-[1.5rem] bg-white/80 p-4">
        <p class="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Evening</p>
        <p class="mt-3 text-sm leading-6 text-[var(--text)]">{{ day.evening || "自由安排" }}</p>
      </section>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { ItineraryDay } from "../types";

defineProps<{
  day: ItineraryDay;
}>();
</script>
