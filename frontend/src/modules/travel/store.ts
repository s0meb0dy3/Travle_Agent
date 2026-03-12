import { reactive, readonly } from "vue";
import type { TravelRequest, TravelResult } from "./types";

type TravelSessionState = {
  request: TravelRequest | null;
  result: TravelResult | null;
  loading: boolean;
  error: string;
  notice: string;
};

const state = reactive<TravelSessionState>({
  request: null,
  result: null,
  loading: false,
  error: "",
  notice: "",
});

export const useTravelSession = () => {
  const setRequest = (request: TravelRequest | null) => {
    state.request = request;
  };

  const setResult = (result: TravelResult | null) => {
    state.result = result;
  };

  const setLoading = (loading: boolean) => {
    state.loading = loading;
  };

  const setError = (error: string) => {
    state.error = error;
  };

  const setNotice = (notice: string) => {
    state.notice = notice;
  };

  const clearNotice = () => {
    state.notice = "";
  };

  return {
    state: readonly(state),
    setRequest,
    setResult,
    setLoading,
    setError,
    setNotice,
    clearNotice,
  };
};
