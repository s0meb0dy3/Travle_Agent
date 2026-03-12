import { createRouter, createWebHistory } from "vue-router";
import HomePage from "../pages/HomePage.vue";
import PlanPage from "../pages/PlanPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomePage,
    },
    {
      path: "/plan",
      name: "plan",
      component: PlanPage,
    },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
