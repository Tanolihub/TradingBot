'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useMarketStore } from '../../stores/market';
import { formatPrice, formatPercent } from '../../lib/format';

function WatchlistRow({ ticker }: { ticker: string }) {
  const quote = useMarketStore((s) => s.quotes[ticker]);
  const activeTicker = useMarketStore((s) => s.activeTicker);
  const setActiveTicker = useMarketStore((s) => s.setActiveTicker);

  const [flash, setFlash] = useState<'up' | 'down' | null>(null);
  const [flashKey, setFlashKey] = useState(0);
  const prevPrice = useRef(quote?.price);

  useEffect(() => {
    if (!quote) return;
    if (prevPrice.current !== undefined && quote.price !== prevPrice.current) {
      setFlash(quote.price > prevPrice.current ? 'up' : 'down');
      setFlashKey((k) => k + 1);
    }
    prevPrice.current = quote.price;
  }, [quote]);

  if (!quote) return null;

  const isActive = activeTicker === ticker;
  const changeColor = quote.change >= 0 ? 'text-up' : 'text-down';

  return (
    <div
      onClick={() => setActiveTicker(ticker)}
      className={`grid grid-cols-[1fr_auto_auto] gap-4 p-2 cursor-pointer border-b border-line/50 hover:bg-raised transition-colors items-center ${isActive ? 'bg-raised border-l-2 border-l-accent' : 'border-l-2 border-l-transparent'}`}
    >
      <span className="font-bold">{ticker}</span>
      <span
        key={flashKey}
        className={`font-mono text-right tabular-nums rounded px-1 min-w-[70px] ${flash === 'up' ? 'tick-up' : flash === 'down' ? 'tick-down' : ''}`}
        onAnimationEnd={() => setFlash(null)}
      >
        {formatPrice(quote.price)}
      </span>
      <span className={`font-mono text-right tabular-nums w-[70px] ${changeColor}`}>
        {formatPercent(quote.change_pct)}
      </span>
    </div>
  );
}

export function Watchlist() {
  const quotes = useMarketStore((s) => s.quotes);
  const tickers = Object.keys(quotes).sort();

  return (
    <aside className="w-full h-full bg-panel rounded-xl border border-line flex flex-col overflow-hidden shadow-xl">
      <div className="p-4 border-b border-line sticky top-0 bg-panel z-10 flex-shrink-0">
        <h2 className="text-sm font-bold text-ink/60 uppercase tracking-wider">Watchlist</h2>
      </div>
      <div className="flex flex-col flex-1 p-2 overflow-y-auto custom-scrollbar">
        {tickers.length === 0 ? (
          <div className="p-4 text-ink/40 text-sm">Waiting for market data...</div>
        ) : (
          tickers.map((t) => <WatchlistRow key={t} ticker={t} />)
        )}
      </div>
    </aside>
  );
}
