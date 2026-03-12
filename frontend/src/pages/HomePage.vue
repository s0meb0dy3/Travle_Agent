<template>
  <main class="shell">
    <div class="mx-auto flex min-h-screen max-w-7xl flex-col gap-12 px-5 py-8 md:px-8 md:py-12">
      <header class="relative z-10 flex items-center justify-between">
        <RouterLink to="/" class="font-display text-2xl font-bold tracking-tight">GoWild</RouterLink>
        <p class="rounded-full border border-[var(--line)] bg-white/70 px-4 py-2 text-xs uppercase tracking-[0.24em] text-[var(--muted)]">
          MVP Frontend
        </p>
      </header>

      <section class="grid items-start gap-8 lg:grid-cols-[1.08fr_0.92fr]">
        <BrandHero />
        <TripForm
          :loading="session.state.loading"
          :error-message="localError"
          :banner="banner"
          @submit="handleSubmit"
        />
      </section>

      <section class="grid gap-4 md:grid-cols-3">
        <div class="glass-card rounded-[1.75rem] p-5">
          <p class="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Fast</p>
          <p class="mt-3 text-lg font-medium">输入几项条件，几分钟拿到第一版路线。</p>
        </div>
        <div class="glass-card rounded-[1.75rem] p-5">
          <p class="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Focused</p>
          <p class="mt-3 text-lg font-medium">不做推荐瀑布流，只给一份可以直接出发的方案。</p>
        </div>
        <div class="glass-card rounded-[1.75rem] p-5">
          <p class="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Readable</p>
          <p class="mt-3 text-lg font-medium">分天行程、预算、提醒一起给清楚，少解释成本。</p>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import BrandHero from "../components/BrandHero.vue";
import TripForm from "../components/TripForm.vue";
import type { TravelRequest } from "../modules/travel/types";
import { useTravelSession } from "../modules/travel/store";
import { generatePlan } from "../services/generatePlan";

const router = useRouter();
const route = useRoute();
const session = useTravelSession();
const localError = ref("");

const banner = computed(() => {
  if (route.query.from === "plan") {
    return "还没有可展示的行程，我们先从首页重新生成一份。";
  }

  return session.state.notice || "";
});

const validateRequest = (request: TravelRequest) => {
  if (!request.origin || !request.destination || !request.days) {
    return "请先填写出发地、目的地和天数。";
  }

  if (!Number.isInteger(request.days) || request.days < 1) {
    return "天数需要是大于 0 的整数。";
  }

  return "";
};

const handleSubmit = async (request: TravelRequest) => {
  localError.value = "";
  session.clearNotice();

  const validationError = validateRequest(request);
  if (validationError) {
    localError.value = validationError;
    return;
  }

  try {
    session.setLoading(true);
    session.setError("");
    session.setRequest(request);
    const result = await generatePlan(request);
    session.setResult(result);
    await router.push("/plan");
  } catch {
    session.setError("这次生成没有成功，请再试一次。");
    localError.value = "这次生成没有成功，请再试一次。";
  } finally {
    session.setLoading(false);
  }
};
</script>
