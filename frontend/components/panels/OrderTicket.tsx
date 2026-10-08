/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useState } from 'react';
import { useMarketStore } from '../../stores/market';
import { formatMoney } from '../../lib/format';

export function OrderTicket() {
  const activeTicker = useMarketStore((s) => s.activeTicker);
  const quote = useMarketStore((s) => s.quotes[activeTicker]);

  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const estimatedCost = (quote?.price || 0) * quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (quantity <= 0) return;

    setLoading(true);
    setError(null);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/api/trades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: activeTicker,
          side,
          quantity,
          idempotency_key: crypto.randomUUID()
        })
      });

      const data = await res.json();
      if (!res.ok) {
        const detail = data.detail;
        if (typeof detail === 'string') {
          setError(detail);
        } else if (detail && typeof detail === 'object' && detail.message) {
          setError(detail.message);
        } else if (Array.isArray(detail)) {
          setError(detail.map((d: any) => d.msg || JSON.stringify(d)).join(', '));
        } else {
          setError('Trade failed');
        }
      } else {
        // Success
        setQuantity(1);
      }
    } catch (err: any) {
      setError(err.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full h-full bg-panel rounded-xl border border-line p-4 flex flex-col gap-4 overflow-hidden shadow-xl">
      <h2 className="text-sm font-bold text-ink/60 uppercase tracking-wider">Manual Order</h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <div className="flex-1 font-bold text-lg bg-raised px-3 py-2 rounded border border-line text-center">
            {activeTicker}
          </div>
        </div>

        <div className="flex p-1 bg-raised rounded border border-line">
          <button
            type="button"
            onClick={() => setSide('buy')}
            className={`flex-1 py-1 text-sm font-bold rounded uppercase transition-colors ${side === 'buy' ? 'bg-up text-white' : 'text-ink/60 hover:text-ink'}`}
          >
            Buy
          </button>
          <button
            type="button"
            onClick={() => setSide('sell')}
            className={`flex-1 py-1 text-sm font-bold rounded uppercase transition-colors ${side === 'sell' ? 'bg-down text-white' : 'text-ink/60 hover:text-ink'}`}
          >
            Sell
          </button>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-ink/60 w-12">Qty</label>
          <input
            type="number"
            min="1"
            step="1"
            value={quantity}
            onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
            className="flex-1 min-w-0 w-full bg-raised border border-line rounded px-3 py-1 font-mono text-black font-bold text-right focus:outline-none focus:border-accent disabled:opacity-50"
          />
        </div>

        <div className="flex justify-between items-center text-sm mt-2">
          <span className="text-ink/60">Est. {side === 'buy' ? 'Cost' : 'Credit'}</span>
          <span className="font-mono">{formatMoney(estimatedCost)}</span>
        </div>

        {error && (
          <div className="text-down text-xs bg-down/10 p-2 rounded border border-down/20">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !quote}
          className="w-full py-2 bg-accent text-black font-bold uppercase rounded hover:bg-accent/90 disabled:opacity-50 transition-colors mt-2"
        >
          {loading ? 'Submitting...' : 'Submit Order'}
        </button>
      </form>
    </div>
  );
}
