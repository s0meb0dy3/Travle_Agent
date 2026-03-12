<template>
  <section class="glass-card rounded-[2rem] p-6">
    <div class="flex items-center justify-between gap-4">
      <div>
        <p class="section-label">Budget</p>
        <p class="mt-4 font-display text-3xl font-bold">{{ summary }}</p>
      </div>
      <div class="rounded-full bg-[rgba(44,182,125,0.15)] px-4 py-2 text-sm font-medium text-[var(--mint)]">
        花费一眼看清
      </div>
    </div>

    <div class="mt-6 grid gap-3">
      <div
        v-for="item in entries"
        :key="item.key"
        class="flex items-center justify-between rounded-[1.35rem] bg-white/80 px-4 py-3 text-sm"
      >
        <span class="text-[var(--muted)]">{{ item.key }}</span>
        <span class="font-medium text-[var(--text)]">{{ item.value }}</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  summary?: string;
  breakdown?: Record<string, string>;
}>();

const entries = computed(() =>
  Object.entries(props.breakdown ?? {}).map(([key, value]) => ({ key, value }))
);
</script>
