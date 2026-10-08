import { useEffect, useRef } from 'react';
import { useMarketStore } from '../stores/market';
import { usePortfolioStore } from '../stores/portfolio';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useStream() {
  const updateQuotes = useMarketStore((s) => s.updateQuotes);
  const updateTicks = useMarketStore((s) => s.updateTicks);
  const updateStatus = useMarketStore((s) => s.updateStatus);
  const updatePortfolio = usePortfolioStore((s) => s.updatePortfolio);

  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const es = new EventSource(`${API_URL}/api/stream`);
      eventSourceRef.current = es;

      es.addEventListener('snapshot', (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.quotes) updateQuotes(data.quotes);
          if (data.status) updateStatus(data.status);
          if (data.portfolio) updatePortfolio(data.portfolio);
        } catch (err) {
          console.error("Failed to parse snapshot:", err);
        }
      });

      es.addEventListener('tick', (e) => {
        try {
          const ticks = JSON.parse(e.data);
          updateTicks(ticks);
        } catch (err) {
          console.error("Failed to parse ticks:", err);
        }
      });

      es.addEventListener('portfolio', (e) => {
        try {
          const portfolio = JSON.parse(e.data);
          updatePortfolio(portfolio);
        } catch (err) {
          console.error("Failed to parse portfolio event:", err);
        }
      });

      es.addEventListener('status', (e) => {
        try {
          const status = JSON.parse(e.data);
          updateStatus(status);
        } catch (err) {
          console.error("Failed to parse status event:", err);
        }
      });

      es.onerror = () => {
        console.warn("EventSource error, reconnecting...");
        es.close();
        updateStatus({ market: 'unknown', feed: 'reconnecting' });
        reconnectTimeout = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [updateQuotes, updateTicks, updateStatus, updatePortfolio]);
}
