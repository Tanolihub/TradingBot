export interface Tick {
  ticker: string;
  price: number;
  change: number;
  change_pct: number;
  ts: string;
}

export interface QuoteSnapshot {
  price: number;
  change: number;
  change_pct: number;
  ts: string;
}

export interface MarketStatus {
  market: string;
  feed: string;
}

export interface PositionSnapshot {
  ticker: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface PortfolioSnapshot {
  cash: number;
  equity: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  positions: PositionSnapshot[];
}

export interface TradeResult {
  id: string;
  ticker: string;
  side: string;
  quantity: number;
  price: number;
  notional: number;
  realized_pnl: number | null;
  executed_at: string;
  source: string;
}
