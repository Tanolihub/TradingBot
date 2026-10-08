'use client';

import React, { useEffect, useState } from 'react';
import { TradeResult } from '../../lib/types';
import { usePortfolioStore } from '../../stores/portfolio';
import { formatTime, formatMoney, formatPrice } from '../../lib/format';

export function TradesTable() {
  const portfolio = usePortfolioStore((s) => s.portfolio);
  const [trades, setTrades] = useState<TradeResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${API_URL}/api/trades?limit=100`)
      .then(r => r.json())
      .then(data => {
        setTrades(data);
        setLoading(false);
      })
      .catch(e => {
        console.error('Failed to fetch trades', e);
        setLoading(false);
      });
  }, [portfolio]); // Re-fetch when portfolio updates (which happens on new trades)

  return (
    <div className="w-full h-full bg-panel rounded-xl border border-line p-4 flex flex-col overflow-hidden shadow-xl">
      <h2 className="text-sm font-bold text-ink/60 mb-4 uppercase tracking-wider flex-shrink-0">Trades</h2>

      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm text-left relative">
          <thead className="text-xs uppercase text-ink/60 bg-panel sticky top-0 z-10">
            <tr>
              <th className="py-2 font-normal">Time</th>
              <th className="py-2 font-normal">Ticker</th>
              <th className="py-2 font-normal">Side</th>
              <th className="py-2 font-normal text-right">Qty</th>
              <th className="py-2 font-normal text-right">Price</th>
              <th className="py-2 font-normal text-right">Notional</th>
              <th className="py-2 font-normal text-right">PnL</th>
              <th className="py-2 font-normal text-right">Source</th>
            </tr>
          </thead>
          <tbody className="font-mono">
            {loading ? (
              <tr><td colSpan={8} className="text-center py-4 text-ink/40">Loading...</td></tr>
            ) : trades.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-4 text-ink/40">No trades yet</td></tr>
            ) : (
              trades.map((t) => (
                <tr key={t.id} className="border-b border-line/30 hover:bg-raised/50">
                  <td className="py-2">{formatTime(t.executed_at)}</td>
                  <td className="py-2 font-bold font-sans">{t.ticker}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded text-xs uppercase ${t.side === 'buy' ? 'bg-up/20 text-up' : 'bg-down/20 text-down'}`}>
                      {t.side}
                    </span>
                  </td>
                  <td className="py-2 text-right tabular-nums">{t.quantity}</td>
                  <td className="py-2 text-right tabular-nums">{formatPrice(t.price)}</td>
                  <td className="py-2 text-right tabular-nums">{formatMoney(t.notional)}</td>
                  <td className="py-2 text-right tabular-nums">
                    {t.realized_pnl !== null ? (
                      <span className={t.realized_pnl > 0 ? 'text-up' : t.realized_pnl < 0 ? 'text-down' : ''}>
                        {formatMoney(t.realized_pnl)}
                      </span>
                    ) : (
                      <span className="text-ink/40">—</span>
                    )}
                  </td>
                  <td className="py-2 text-right">
                    <span className="px-2 py-0.5 rounded text-xs uppercase bg-raised text-ink/60">
                      {t.source}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
