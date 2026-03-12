import type { TravelRequest, TravelResult } from "../modules/travel/types";

export const generatePlan = async (request: TravelRequest): Promise<TravelResult> => {
  const response = await fetch("/api/v1/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let message = "generate plan failed";

    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail || message;
    } catch {
      // Ignore JSON parsing failures and fall back to the generic error.
    }

    throw new Error(message);
  }

  return response.json() as Promise<TravelResult>;
};
