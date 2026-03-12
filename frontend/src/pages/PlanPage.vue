<template>
  <main class="shell">
    <div class="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-5 py-8 md:px-8 md:py-10">
      <header class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <RouterLink to="/" class="font-display text-2xl font-bold tracking-tight">GoWild</RouterLink>
        <div class="flex flex-wrap gap-3">
          <button
            type="button"
            class="rounded-full border border-[var(--line)] bg-white/80 px-5 py-3 text-sm font-medium text-[var(--text)] transition hover:border-[var(--text)]"
            @click="copyPlan"
          >
            {{ copyLabel }}
          </button>
          <RouterLink
            to="/"
            class="rounded-full bg-[var(--text)] px-5 py-3 text-sm font-medium text-white transition hover:bg-black"
          >
            重新生成
          </RouterLink>
        </div>
      </header>

      <div v-if="session.state.error" class="rounded-[1.5rem] border border-[rgba(242,65,16,0.18)] bg-[rgba(242,65,16,0.10)] px-4 py-3 text-sm text-[var(--text)]">
        {{ session.state.error }}
      </div>

      <PlanSummary v-if="request && result" :request="request" :result="result" />

      <section v-if="result" class="grid gap-5">
        <ItineraryCard v-for="day in result.plan.days" :key="day.day" :day="day" />
      </section>

      <section v-if="result" class="grid gap-5 lg:grid-cols-[0.92fr_1.08fr]">
        <BudgetSummary
          :summary="result.plan.budgetSummary"
          :breakdown="result.plan.budgetBreakdown"
        />
        <TipsList :tips="result.tips ?? []" />
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import BudgetSummary from "../modules/travel/components/BudgetSummary.vue";
import ItineraryCard from "../modules/travel/components/ItineraryCard.vue";
import PlanSummary from "../modules/travel/components/PlanSummary.vue";
import TipsList from "../modules/travel/components/TipsList.vue";
import { useTravelSession } from "../modules/travel/store";

const router = useRouter();
const session = useTravelSession();
const copyLabel = ref("复制结果");

const request = computed(() => session.state.request);
const result = computed(() => session.state.result);

onMounted(() => {
  if (!request.value || !result.value) {
    router.replace({ path: "/", query: { from: "plan" } });
  }
});

const copyPlan = async () => {
  if (!request.value || !result.value) {
    return;
  }

  const lines = [
    `${result.value.summary}`,
    `出发地：${request.value.origin}`,
    `目的地：${request.value.destination}`,
    `天数：${request.value.days} 天`,
    request.value.budget ? `预算：${request.value.budget}` : "",
    "",
    ...result.value.plan.days.flatMap((day) => [
      `Day ${day.day}｜${day.title}`,
      `上午：${day.morning ?? "自由安排"}`,
      `下午：${day.afternoon ?? "自由安排"}`,
      `晚上：${day.evening ?? "自由安排"}`,
      "",
    ]),
    `预算摘要：${result.value.plan.budgetSummary ?? "待定"}`,
    ...Object.entries(result.value.plan.budgetBreakdown ?? {}).map(
      ([key, value]) => `${key}：${value}`
    ),
    "",
    "注意事项：",
    ...(result.value.tips ?? []).map((tip, index) => `${index + 1}. ${tip}`),
  ].filter(Boolean);

  try {
    await navigator.clipboard.writeText(lines.join("\n"));
    copyLabel.value = "复制成功";
    window.setTimeout(() => {
      copyLabel.value = "复制结果";
    }, 1800);
  } catch {
    copyLabel.value = "复制失败";
    window.setTimeout(() => {
      copyLabel.value = "复制结果";
    }, 1800);
  }
};
</script>
