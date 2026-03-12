<template>
  <section class="glass-card rounded-[2rem] p-6">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <p class="section-label">Trip Brief</p>
        <h1 class="font-display mt-4 text-3xl font-bold md:text-4xl">{{ result.summary }}</h1>
        <p class="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">
          从 {{ request.origin }} 出发，去 {{ request.destination }} 待 {{ request.days }} 天
          <span v-if="request.budget">，预算目标 {{ request.budget }}</span>
          <span v-if="request.style?.length">，偏好 {{ styleText }}</span>
        </p>
      </div>

      <div class="rounded-[1.5rem] bg-white/80 px-4 py-3 text-sm text-[var(--text)]">
        <p class="font-medium">当前需求摘要</p>
        <p class="mt-2 text-[var(--muted)]">{{ request.prompt || "没有额外补充，按基础旅行信息生成。" }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { TravelRequest, TravelResult } from "../types";

const props = defineProps<{
  request: TravelRequest;
  result: TravelResult;
}>();

const styleText = computed(() => props.request.style?.join(" / ") ?? "默认节奏");
</script>
