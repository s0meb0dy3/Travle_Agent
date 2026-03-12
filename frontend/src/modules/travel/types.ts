export type TravelRequest = {
  origin: string;
  destination: string;
  days: number;
  budget?: string;
  style?: readonly string[];
  prompt?: string;
};

export type ItineraryDay = {
  day: number;
  title: string;
  morning?: string;
  afternoon?: string;
  evening?: string;
};

export type TravelResult = {
  mode: "itinerary";
  summary: string;
  plan: {
    days: readonly ItineraryDay[];
    budgetSummary?: string;
    budgetBreakdown?: Record<string, string>;
  };
  tips?: readonly string[];
};
