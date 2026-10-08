import { create } from 'zustand';
import { PortfolioSnapshot } from '../lib/types';

interface PortfolioState {
  portfolio: PortfolioSnapshot | null;
  updatePortfolio: (portfolio: PortfolioSnapshot) => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  portfolio: null,
  updatePortfolio: (portfolio) => set({ portfolio }),
}));
