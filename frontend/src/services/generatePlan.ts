import { planTemplates } from "../modules/travel/mockData";
import type { TravelRequest, TravelResult } from "../modules/travel/types";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const generatePlan = async (request: TravelRequest): Promise<TravelResult> => {
  await wait(900);

  if (request.destination.trim() === "故障测试") {
    throw new Error("mock service unavailable");
  }

  const template = planTemplates.find((item) => item.matches(request));
  if (!template) {
    throw new Error("no plan template");
  }

  return template.build(request);
};
