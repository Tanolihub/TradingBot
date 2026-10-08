/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
'use client';

import React, { useMemo } from 'react';
import { usePortfolioStore } from '../../stores/portfolio';
import * as d3 from 'd3-hierarchy';
import { formatPercent, formatMoney } from '../../lib/format';

interface HeatmapNode {
  name: string;
  value: number; // market value
  pnlPct: number;
}

export function PortfolioHeatmap() {
  const portfolio = usePortfolioStore((s) => s.portfolio);

  const rootNode = useMemo(() => {
    if (!portfolio || portfolio.positions.length === 0) return null;

    // Create hierarchy
    const root = { name: 'root', children: portfolio.positions.map(p => ({
      name: p.ticker,
      value: p.market_value,
      pnlPct: p.unrealized_pnl_pct
    })) as HeatmapNode[] };

    const hierarchy = d3.hierarchy<any>(root).sum((d: any) => d.value || 0);

    // We'll compute the layout dynamically based on container size using relative percentages
    // by using a fixed virtual size (100x100) and then doing absolute % positioning.
    d3.treemap<HeatmapNode>().size([100, 100]).padding(1).round(false)(hierarchy as any);

    return hierarchy;
  }, [portfolio]);

  if (!portfolio) {
    return (
      <div className="w-full h-full bg-panel rounded-xl border border-line p-4 flex flex-col overflow-hidden shadow-xl">
        <h2 className="text-sm font-bold text-ink/60 mb-2 uppercase tracking-wider">Positions</h2>
        <div className="flex-1 flex items-center justify-center text-ink/40 text-sm">Loading portfolio...</div>
      </div>
    );
  }

  if (portfolio.positions.length === 0) {
    return (
      <div className="w-full h-full bg-panel rounded-xl border border-line p-4 flex flex-col overflow-hidden shadow-xl">
        <h2 className="text-sm font-bold text-ink/60 mb-2 uppercase tracking-wider">Positions</h2>
        <div className="flex-1 flex items-center justify-center text-ink/40 text-sm">No open positions</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-panel rounded-xl border border-line p-4 flex flex-col overflow-hidden shadow-xl">
      <h2 className="text-sm font-bold text-ink/60 mb-4 uppercase tracking-wider flex-shrink-0">Portfolio Heatmap</h2>
      <div className="flex-1 relative w-full h-full rounded overflow-hidden">
        {rootNode && rootNode.leaves().map((leaf: any, i) => {
          const data = leaf.data as HeatmapNode;
          // Determine color based on PnL pct
          // We will use standard up/down colors but vary opacity based on magnitude
          const isUp = data.pnlPct >= 0;
          const absPct = Math.min(Math.abs(data.pnlPct), 10); // cap at 10% for color intensity
          const opacity = 0.2 + (absPct / 10) * 0.8; // range 0.2 to 1.0
          const bgColor = isUp ? `rgba(34, 197, 94, ${opacity})` : `rgba(239, 68, 68, ${opacity})`;

          return (
            <div
              key={data.name}
              className="absolute border border-bg overflow-hidden flex flex-col items-center justify-center text-white"
              style={{
                left: `${leaf.x0}%`,
                top: `${leaf.y0}%`,
                width: `${leaf.x1 - leaf.x0}%`,
                height: `${leaf.y1 - leaf.y0}%`,
                backgroundColor: bgColor,
              }}
              title={`${data.name}\nValue: ${formatMoney(data.value)}\nPnL: ${formatPercent(data.pnlPct)}`}
            >
              <span className="font-bold text-sm mix-blend-overlay">{data.name}</span>
              {(leaf.x1 - leaf.x0 > 15 && leaf.y1 - leaf.y0 > 15) && (
                <span className="text-xs font-mono opacity-80">{formatPercent(data.pnlPct)}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
