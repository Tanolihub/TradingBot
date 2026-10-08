'use client';

import React from 'react';
import { usePortfolioStore } from '../../stores/portfolio';
import { useMarketStore } from '../../stores/market';
import { formatMoney, formatPercent } from '../../lib/format';
import { Power, PowerOff, RefreshCw } from 'lucide-react';

export function TopBar() {
  const portfolio = usePortfolioStore((s) => s.portfolio);
  const status = useMarketStore((s) => s.status);

  const handleReset = async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      await fetch(`${API_URL}/api/portfolio/reset`, { method: 'POST' });
    } catch (e) {
      console.error('Failed to reset', e);
    }
  };

  const isFeedUp = status.feed === 'connected';

  return (
    <header className="w-full h-full bg-panel rounded-xl border border-line p-4 flex items-center justify-between shadow-xl">
      <div className="flex flex-col">
        <h1 className="font-bold text-accent tracking-wide uppercase leading-tight text-lg">NeonPulse AI</h1>
        <span className="text-[10px] font-mono text-accent/80 uppercase tracking-widest mt-0.5">
          Simulated Trading
        </span>
      </div>

      <div className="flex items-center gap-6 font-mono text-sm">
        <div className="flex flex-col text-right">
          <span className="text-accent/50 text-xs">EQUITY</span>
          <span className="font-bold">{portfolio ? formatMoney(portfolio.equity) : '—'}</span>
        </div>
        <div className="flex flex-col text-right border-l border-line pl-6">
          <span className="text-accent/50 text-xs">CASH</span>
          <span>{portfolio ? formatMoney(portfolio.cash) : '—'}</span>
        </div>
        <div className="flex flex-col text-right border-l border-line pl-6">
          <span className="text-accent/50 text-xs">UNREALIZED P&L</span>
          {portfolio ? (
            <span className={portfolio.unrealized_pnl > 0 ? 'text-up' : portfolio.unrealized_pnl < 0 ? 'text-down' : ''}>
              {formatMoney(portfolio.unrealized_pnl)} ({formatPercent(portfolio.unrealized_pnl_pct)})
            </span>
          ) : (
            <span>—</span>
          )}
        </div>

        <div className="border-l border-line pl-6 flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-accent/50 text-xs uppercase text-right">Market: {status.market}</span>
            <div className={`flex items-center gap-2 text-xs uppercase ${isFeedUp ? 'text-up' : 'text-down'}`}>
              {isFeedUp ? <Power className="w-3 h-3" /> : <PowerOff className="w-3 h-3" />}
              {status.feed}
            </div>
          </div>

          <button
            onClick={handleReset}
            className="p-2 hover:bg-raised rounded text-ink/60 hover:text-accent transition-colors"
            title="Reset Portfolio"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
