<template>
  <form class="glass-card fade-rise relative z-10 rounded-[2rem] p-5 md:p-8" @submit.prevent="submitForm">
    <div class="flex items-center justify-between gap-4">
      <div>
        <p class="font-display text-2xl font-bold text-[var(--text)]">开始一趟刚刚好的旅行</p>
        <p class="mt-2 text-sm leading-6 text-[var(--muted)]">只填必要信息，生成一版可直接看的短途出游方案。</p>
      </div>
      <div class="hidden rounded-full bg-[rgba(255,209,102,0.35)] px-4 py-2 text-xs font-medium text-[var(--text)] md:block">
        MVP / Mock Ready
      </div>
    </div>

    <div v-if="banner" class="mt-6 rounded-2xl border border-[rgba(28,167,236,0.16)] bg-[rgba(28,167,236,0.10)] px-4 py-3 text-sm text-[var(--text)]">
      {{ banner }}
    </div>

    <div class="mt-6 grid gap-4 md:grid-cols-2">
      <label class="space-y-2">
        <span class="text-sm font-medium text-[var(--text)]">出发地</span>
        <input
          v-model.trim="form.origin"
          class="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--sky)]"
          placeholder="比如 上海"
        />
      </label>

      <label class="space-y-2">
        <span class="text-sm font-medium text-[var(--text)]">目的地</span>
        <input
          v-model.trim="form.destination"
          class="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--brand)]"
          placeholder="比如 杭州"
        />
      </label>

      <label class="space-y-2">
        <span class="text-sm font-medium text-[var(--text)]">天数</span>
        <input
          v-model.number="form.days"
          min="1"
          max="7"
          type="number"
          class="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--mint)]"
          placeholder="2"
        />
      </label>

      <label class="space-y-2">
        <span class="text-sm font-medium text-[var(--text)]">预算</span>
        <input
          v-model.trim="form.budget"
          class="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--sun)]"
          placeholder="比如 1000-1500 / 人"
        />
      </label>
    </div>

    <fieldset class="mt-5">
      <legend class="text-sm font-medium text-[var(--text)]">风格偏好</legend>
      <div class="mt-3 flex flex-wrap gap-3">
        <button
          v-for="item in styleOptions"
          :key="item.value"
          type="button"
          class="rounded-full border px-4 py-2 text-sm transition"
          :class="selectedStyles.includes(item.value)
            ? 'border-[var(--text)] bg-[var(--text)] text-white'
            : 'border-[var(--line)] bg-white/70 text-[var(--text)] hover:border-[var(--text)]'"
          @click="toggleStyle(item.value)"
        >
          {{ item.label }}
        </button>
      </div>
    </fieldset>

    <label class="mt-5 block space-y-2">
      <span class="text-sm font-medium text-[var(--text)]">还有什么希望被考虑进来？</span>
      <textarea
        v-model.trim="form.prompt"
        rows="4"
        class="w-full rounded-[1.6rem] border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--brand)]"
        placeholder="比如：周末想透透气，不想太赶，最好适合拍照和好吃的。"
      />
    </label>

    <div v-if="errorMessage" class="mt-4 rounded-2xl border border-[rgba(242,65,16,0.18)] bg-[rgba(242,65,16,0.10)] px-4 py-3 text-sm text-[var(--text)]">
      {{ errorMessage }}
    </div>

    <div class="mt-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <p class="text-sm leading-6 text-[var(--muted)]">
        推荐先从 2 天 1 夜开始，首版更适合国内短途和周末出行。
      </p>

      <button
        type="submit"
        class="inline-flex items-center justify-center rounded-full bg-[var(--text)] px-6 py-3 font-medium text-white transition hover:translate-y-[-1px] hover:bg-black disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="loading"
      >
        {{ loading ? "正在生成中..." : "开始生成" }}
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { computed, reactive } from "vue";
import type { TravelRequest } from "../modules/travel/types";

const props = defineProps<{
  loading: boolean;
  errorMessage: string;
  banner?: string;
}>();

const emit = defineEmits<{
  submit: [request: TravelRequest];
}>();

const styleOptions = [
  { label: "轻松", value: "relaxed" },
  { label: "拍照", value: "photogenic" },
  { label: "美食", value: "foodie" },
  { label: "City Walk", value: "city walk" },
  { label: "自然感", value: "nature" },
];

const form = reactive<TravelRequest>({
  origin: "上海",
  destination: "杭州",
  days: 2,
  budget: "1000-1500",
  style: ["relaxed", "photogenic"],
  prompt: "周末想透透气，不想太累。"
});

const selectedStyles = computed(() => form.style ?? []);

const toggleStyle = (value: string) => {
  const current = new Set(form.style ?? []);

  if (current.has(value)) {
    current.delete(value);
  } else {
    current.add(value);
  }

  form.style = Array.from(current);
};

const submitForm = () => {
  emit("submit", {
    origin: form.origin.trim(),
    destination: form.destination.trim(),
    days: Number(form.days),
    budget: form.budget?.trim() || undefined,
    style: form.style?.length ? form.style : undefined,
    prompt: form.prompt?.trim() || undefined,
  });
};
</script>
