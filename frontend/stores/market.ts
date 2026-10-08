import { create } from 'zustand';
import { QuoteSnapshot, MarketStatus, Tick } from '../lib/types';

interface MarketState {
  quotes: Record<string, QuoteSnapshot>;
  status: MarketStatus;
  activeTicker: string;
  updateQuotes: (quotes: Record<string, QuoteSnapshot>) => void;
  updateTicks: (ticks: Tick[]) => void;
  updateStatus: (status: MarketStatus) => void;
  setActiveTicker: (ticker: string) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  quotes: {},
  status: { market: 'unknown', feed: 'unknown' },
  activeTicker: 'AAPL',
  updateQuotes: (quotes) => set({ quotes }),
  updateTicks: (ticks) =>
    set((state) => {
      const newQuotes = { ...state.quotes };
      for (const tick of ticks) {
        newQuotes[tick.ticker] = {
          price: tick.price,
          change: tick.change,
          change_pct: tick.change_pct,
          ts: tick.ts,
        };
      }
      return { quotes: newQuotes };
    }),
  updateStatus: (status) => set({ status }),
  setActiveTicker: (ticker) => set({ activeTicker: ticker }),
}));
