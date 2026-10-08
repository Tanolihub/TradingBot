'use client';

import dynamic from 'next/dynamic';

const PriceChartInner = dynamic(() => import('./PriceChartInner'), {
  ssr: false,
  loading: () => (
    <main className="glow-radial flex flex-col p-4 overflow-hidden h-full">
      <h2 className="text-sm font-bold text-ink/60 mb-2 uppercase tracking-wider">Chart</h2>
      <div className="flex-1 animate-pulse bg-raised/50 rounded border border-line flex items-center justify-center">
        <span className="text-ink/40 font-mono text-sm">Loading Chart Engine...</span>
      </div>
    </main>
  ),
});

export function PriceChart() {
  return <PriceChartInner />;
}
