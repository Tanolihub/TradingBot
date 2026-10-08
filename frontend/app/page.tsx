import React from 'react';
import { StreamInitializer } from '../components/StreamInitializer';
import { TopBar } from '../components/panels/TopBar';
import { Watchlist } from '../components/panels/Watchlist';
import { PriceChart } from '../components/panels/PriceChart';
import { PortfolioHeatmap } from '../components/panels/PortfolioHeatmap';
import { TradesTable } from '../components/panels/TradesTable';
import { OrderTicket } from '../components/panels/OrderTicket';
import { AiChat } from '../components/panels/AiChat';

export default function Home() {
  return (
    <div className="flex flex-col h-[100dvh] w-full p-4 gap-4 overflow-hidden">
      <StreamInitializer />

      <div className="flex-shrink-0">
        <TopBar />
      </div>

      <div className="flex-1 grid grid-cols-[300px_1fr_350px] gap-4 min-h-0">
        {/* Left Column */}
        <div className="flex flex-col gap-4 h-full min-h-0">
          <div className="flex-1 min-h-0">
            <Watchlist />
          </div>
          <div className="flex-shrink-0">
            <OrderTicket />
          </div>
        </div>

        {/* Middle Column */}
        <div className="flex flex-col gap-4 h-full min-w-0">
          <div className="flex-1 min-h-0">
             <PriceChart />
          </div>
          <div className="h-[280px] flex gap-4 flex-shrink-0">
             <div className="w-[300px] flex-shrink-0">
                <PortfolioHeatmap />
             </div>
             <div className="flex-1 min-w-0">
                <TradesTable />
             </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="flex flex-col h-full min-h-0">
          <div className="flex-1 min-h-0">
            <AiChat />
          </div>
        </div>
      </div>
    </div>
  );
}
