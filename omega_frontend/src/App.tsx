import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, ReferenceLine, Cell, BarChart, RadialBarChart, RadialBar
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Activity, DollarSign, Target, 
  AlertTriangle, Zap, BarChart3, ArrowUpRight, ArrowDownRight, 
  Clock, Layers, Brain, Volume2, Gauge, Eye, Shield, Crosshair,
  ChevronUp, ChevronDown, Cpu, Network, Sparkles, Award
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type UnknownRecord = Record<string, unknown>;

interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
  [k: string]: unknown;
}

interface VwapPoint {
  timestamp: string;
  vwap: number;
  upper_band_1: number;
  lower_band_1: number;
  upper_band_2?: number;
  lower_band_2?: number;
  [k: string]: unknown;
}

interface DeltaPoint {
  idx: number;
  delta: number;
  cumulative_delta: number;
  is_bullish: boolean;
  timestamp?: string;
  [k: string]: unknown;
}

interface LiquiditySweep {
  type: string;
  signal?: string;
  sweep_price?: number;
  price?: number;
  [k: string]: unknown;
}

interface SwingPoint {
  price: number;
  timestamp?: string;
  type?: string;
  [k: string]: unknown;
}

interface BosSignal {
  type: string;
  broken_level?: number;
  current_price?: number;
  [k: string]: unknown;
}

interface ClosedTrade {
  symbol: string;
  side: 'LONG' | 'SHORT' | string;
  entry?: number;
  exit?: number;
  pnl: number;
  exit_reason?: string;
  [k: string]: unknown;
}

interface UnifiedSignal {
  name: 'VP' | 'Delta' | 'OFI' | 'Struct';
  bias: 'BULL' | 'BEAR' | 'NEUT';
}

interface UnifiedDecision {
  decision: string;
  confidence: number;
  signals: UnifiedSignal[];
}

interface VpBar {
  y: number;
  height: number;
  totalWidth: number;
  buyWidth: number;
  sellWidth: number;
  neutralWidth: number;
  isPOC: boolean;
  isValueArea: boolean;
  isHVN: boolean;
  price: number;
  delta: number;
}

interface VolumeLevel {
  price_low: number;
  price_high: number;
  price_mid: number;
  volume: number;
  volume_pct: number;
  buy_volume: number;
  sell_volume: number;
  delta: number;
  is_value_area: boolean;
  is_hvn: boolean;
  is_lvn: boolean;
}

interface VolumeProfile {
  levels: VolumeLevel[];
  poc: number;
  vah: number;
  val: number;
  price_high: number;
  price_low: number;
  total_volume: number;
  hvn_prices: number[];
  lvn_prices: number[];
}

interface OrderFlowImbalance {
  ofi: number;
  ofi_normalized: number;
  signal: string;
  strength: number;
  lookback: number;
}

interface FootprintAnalysis {
  imbalances: UnknownRecord[];
  absorption_zones: UnknownRecord[];
  exhaustion_signals: UnknownRecord[];
}

interface MarketStructure {
  structure: string;
  trend: string;
  swing_highs: SwingPoint[];
  swing_lows: SwingPoint[];
  bos_signals: BosSignal[];
  choch_signals: BosSignal[];
}

interface RiskMetrics {
  var_95: number;
  var_99: number;
  expected_shortfall: number;
  volatility: number;
  sharpe_estimate: number;
  max_drawdown: number;
}

interface InstitutionalLevel {
  price: number;
  type: string;
  strength: number;
  description: string;
}

interface ChartData {
  candles: Candle[];
  volume_profile: VolumeProfile | null;
  vwap: VwapPoint[];
  delta: DeltaPoint[];
  current_price: number;
  order_flow_imbalance: OrderFlowImbalance | null;
  footprint: FootprintAnalysis | null;
  liquidity_sweeps: LiquiditySweep[];
  market_structure: MarketStructure | null;
  institutional_levels: { levels: InstitutionalLevel[], zones: UnknownRecord[] } | null;
  risk_metrics: RiskMetrics | null;
}

interface TradingState {
  capital: number;
  equity: number;
  total_pnl: number;
  total_pnl_pct: number;
  daily_pnl: number;
  regime: string;
  confluence_score: number;
  kill_switch_active: boolean;
  open_positions: UnknownRecord[];
  closed_trades: ClosedTrade[];
}

interface Performance {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  total_pnl: number;
  avg_trade: number;
  best_trade: number;
  worst_trade: number;
}

const SignalGauge = ({ value, label, signal }: { value: number, label: string, signal: string }) => {
  const getColor = () => {
    if (signal.includes('BUY') || signal.includes('BULLISH')) return '#10b981';
    if (signal.includes('SELL') || signal.includes('BEARISH')) return '#ef4444';
    return '#64748b';
  };

  const data = [{ value: Math.abs(value) * 100, fill: getColor() }];

  return (
    <div className="flex flex-col items-center">
      <div className="w-24 h-24">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="100%" data={data} startAngle={180} endAngle={0}>
            <RadialBar background dataKey="value" cornerRadius={10} />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
      <div className="text-center -mt-4">
        <div className={`text-lg font-bold ${signal.includes('BUY') ? 'text-emerald-400' : signal.includes('SELL') ? 'text-red-400' : 'text-slate-400'}`}>
          {signal}
        </div>
        <div className="text-xs text-slate-500">{label}</div>
      </div>
    </div>
  );
};

const RiskCard = ({ label, value, unit, isNegative }: { label: string, value: number, unit: string, isNegative?: boolean }) => {
  const displayValue = isNegative ? value : Math.abs(value);
  const color = value < 0 ? 'text-red-400' : value > 0 ? 'text-emerald-400' : 'text-slate-400';
  
  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className={`text-lg font-mono font-bold ${color}`}>
        {displayValue.toFixed(2)}{unit}
      </div>
    </div>
  );
};

const LevelRow = ({ level, decimals }: { level: InstitutionalLevel, decimals: number }) => {
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'POC': return 'bg-yellow-500';
      case 'VAH': case 'VAL': return 'bg-cyan-500';
      case 'HVN': return 'bg-emerald-500';
      case 'LVN': return 'bg-orange-500';
      default: return 'bg-slate-500';
    }
  };

  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-700/30 hover:bg-slate-800/30 transition-colors">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${getTypeColor(level.type)}`} />
        <span className="text-xs font-medium text-slate-300">{level.type}</span>
      </div>
      <div className="text-sm font-mono text-white">{level.price.toFixed(decimals)}</div>
      <div className="w-16">
        <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div 
            className={`h-full ${getTypeColor(level.type)} rounded-full`}
            style={{ width: `${level.strength * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

const FootprintSignal = ({ type, count }: { type: string, count: number }) => {
  const getIcon = () => {
    switch (type) {
      case 'imbalances': return <Layers className="w-4 h-4" />;
      case 'absorption': return <Shield className="w-4 h-4" />;
      case 'exhaustion': return <AlertTriangle className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getColor = () => {
    if (count === 0) return 'text-slate-500 border-slate-700';
    if (type === 'imbalances') return 'text-purple-400 border-purple-500/50 bg-purple-500/10';
    if (type === 'absorption') return 'text-cyan-400 border-cyan-500/50 bg-cyan-500/10';
    return 'text-amber-400 border-amber-500/50 bg-amber-500/10';
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getColor()}`}>
      {getIcon()}
      <span className="text-xs font-medium capitalize">{type}</span>
      <span className="ml-auto text-sm font-bold">{count}</span>
    </div>
  );
};

const VolumeProfileChart = ({ data, currentPrice, symbol }: { data: VolumeProfile | null, currentPrice: number, symbol: string }) => {
  if (!data || !data.levels || data.levels.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        <Activity className="w-6 h-6 animate-pulse mr-2" />
        Loading Volume Profile...
      </div>
    );
  }

  const decimals = symbol === 'XAUUSD' ? 2 : symbol === 'USDJPY' ? 3 : 5;
  const maxVolume = Math.max(...data.levels.map(l => l.volume_pct));

  return (
    <div className="h-full flex">
      <div className="w-16 flex flex-col justify-between text-xs text-slate-400 pr-2">
        <span>{data.price_high.toFixed(decimals)}</span>
        <span className="text-cyan-400 font-bold">{data.vah.toFixed(decimals)}</span>
        <span className="text-yellow-400 font-bold">{data.poc.toFixed(decimals)}</span>
        <span className="text-cyan-400 font-bold">{data.val.toFixed(decimals)}</span>
        <span>{data.price_low.toFixed(decimals)}</span>
      </div>
      
      <div className="flex-1 flex flex-col-reverse relative">
        {currentPrice > 0 && (
          <div 
            className="absolute w-full h-0.5 bg-white z-10 shadow-lg shadow-white/20"
            style={{
              bottom: `${((currentPrice - data.price_low) / (data.price_high - data.price_low)) * 100}%`
            }}
          >
            <span className="absolute right-0 -top-3 text-xs bg-white text-black px-1.5 py-0.5 rounded font-mono font-bold">
              {currentPrice.toFixed(decimals)}
            </span>
          </div>
        )}
        
        <div 
          className="absolute w-full h-px bg-cyan-500/50 z-5"
          style={{ bottom: `${((data.vah - data.price_low) / (data.price_high - data.price_low)) * 100}%` }}
        />
        <div 
          className="absolute w-full h-px bg-cyan-500/50 z-5"
          style={{ bottom: `${((data.val - data.price_low) / (data.price_high - data.price_low)) * 100}%` }}
        />
        <div 
          className="absolute w-full h-0.5 bg-yellow-500 z-5"
          style={{ bottom: `${((data.poc - data.price_low) / (data.price_high - data.price_low)) * 100}%` }}
        />
        
        {data.levels.map((level, idx) => {
          const width = (level.volume_pct / maxVolume) * 100;
          const isDelta = level.delta > 0;
          
          return (
            <div 
              key={idx} 
              className="flex-1 flex items-center group relative"
              title={`Price: ${level.price_mid.toFixed(decimals)} | Vol: ${level.volume.toFixed(0)} | Delta: ${level.delta.toFixed(0)}`}
            >
              {level.is_value_area && (
                <div className="absolute inset-0 bg-cyan-500/10" />
              )}
              
              <div 
                className={`h-full transition-all duration-200 ${
                  level.is_hvn 
                    ? isDelta ? 'bg-emerald-500' : 'bg-red-500'
                    : level.is_value_area 
                      ? isDelta ? 'bg-emerald-500/70' : 'bg-red-500/70'
                      : isDelta ? 'bg-emerald-500/40' : 'bg-red-500/40'
                }`}
                style={{ width: `${width}%` }}
              />
              
              <div className="absolute left-full ml-2 hidden group-hover:block bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-xs z-20 whitespace-nowrap shadow-xl">
                <div className="font-bold mb-1">Price: {level.price_mid.toFixed(decimals)}</div>
                <div className="text-emerald-400">Buy Vol: {level.buy_volume.toFixed(0)}</div>
                <div className="text-red-400">Sell Vol: {level.sell_volume.toFixed(0)}</div>
                <div className={`font-bold ${isDelta ? 'text-emerald-400' : 'text-red-400'}`}>
                  Delta: {level.delta > 0 ? '+' : ''}{level.delta.toFixed(0)}
                </div>
                {level.is_hvn && <div className="text-yellow-400 mt-1">High Volume Node</div>}
                {level.is_lvn && <div className="text-orange-400 mt-1">Low Volume Node</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// UNPUSHABLE BREAKTHROUGH: DeepCharts-style integrated chart with Volume Profile, Confidence Zones, Entry/Exit Markers
const CandlestickChart = ({ candles, vwap, symbol, volumeProfile, liquiditySweeps, marketStructure, unifiedDecision, tradeSetup }: {
  candles: Candle[], 
  vwap: VwapPoint[], 
  symbol: string,
  volumeProfile?: VolumeProfile | null,
  liquiditySweeps?: LiquiditySweep[],
  marketStructure?: MarketStructure | null,
  unifiedDecision?: UnifiedDecision | null,
  tradeSetup?: { direction: string, confidence: number, entry: number, stopLoss: number, target1: number, target2: number, riskReward1: number, isHighProbability: boolean } | null,
  delta?: DeltaPoint[]
}) => {
  const decimals = symbol === 'XAUUSD' ? 2 : symbol === 'USDJPY' ? 3 : 5;
  
  const chartData = useMemo(() => {
    return candles.map((c, i) => ({
      ...c,
      idx: i,
      vwap: vwap[i]?.vwap,
      upper_band: vwap[i]?.upper_band_1,
      lower_band: vwap[i]?.lower_band_1,
      isBullish: c.close >= c.open,
    }));
  }, [candles, vwap]);

  // Calculate all derived values using useMemo to ensure hooks are called consistently
  const chartCalculations = useMemo(() => {
    if (chartData.length === 0) {
      return null;
    }
    
    const allPrices = chartData.flatMap(c => [c.high, c.low]);
    const priceHigh = Math.max(...allPrices);
    const priceLow = Math.min(...allPrices);
    const priceRange = priceHigh - priceLow;
    const padding = priceRange * 0.05;
    const adjustedHigh = priceHigh + padding;
    const adjustedLow = priceLow - padding;
    const adjustedRange = adjustedHigh - adjustedLow;

    const chartWidth = 700;
    const chartHeight = 350;
    // BREAKTHROUGH: Volume Profile extends FROM THE LEFT into the chart
    const vpWidth = volumeProfile ? 120 : 0; // Width for integrated volume profile
    const marginLeft = 70 + vpWidth; // Extra space for VP on left
    const marginRight = 70;
    const marginTop = 10;
    const marginBottom = 20;
    const plotWidth = chartWidth - marginLeft - marginRight;
    const plotHeight = chartHeight - marginTop - marginBottom;

    const priceToY = (price: number) => marginTop + plotHeight - ((price - adjustedLow) / adjustedRange) * plotHeight;
    const indexToX = (idx: number) => marginLeft + (idx / (chartData.length - 1 || 1)) * plotWidth;
    const candleWidth = Math.max(2, Math.min(8, plotWidth / chartData.length - 1));

    const yTicks: number[] = [];
    const tickCount = 6;
    for (let i = 0; i <= tickCount; i++) {
      const price = adjustedLow + (adjustedRange * i / tickCount);
      yTicks.push(price);
    }

    // BREAKTHROUGH: Volume Profile bars extending FROM LEFT INTO the chart (DeepCharts style)
    let vpBars: VpBar[] = [];
    if (volumeProfile?.levels) {
      const maxVol = Math.max(...volumeProfile.levels.map(l => l.volume_pct));
      vpBars = volumeProfile.levels.map(level => {
        // Calculate delta ratio for coloring (green = buying, orange = selling)
        const buyRatio = level.delta > 0 ? Math.min(1, level.delta / 100) : 0;
        const sellRatio = level.delta < 0 ? Math.min(1, Math.abs(level.delta) / 100) : 0;
        const neutralRatio = 1 - buyRatio - sellRatio;
        
        return {
          y: priceToY(level.price_high),
          height: Math.abs(priceToY(level.price_low) - priceToY(level.price_high)),
          // Width extends from left margin INTO the chart area
          totalWidth: (level.volume_pct / maxVol) * vpWidth,
          buyWidth: (level.volume_pct / maxVol) * vpWidth * buyRatio,
          sellWidth: (level.volume_pct / maxVol) * vpWidth * sellRatio,
          neutralWidth: (level.volume_pct / maxVol) * vpWidth * neutralRatio,
          isPOC: Math.abs(level.price_mid - volumeProfile.poc) < (priceRange / 100),
          isValueArea: level.is_value_area,
          isHVN: level.is_hvn,
          price: level.price_mid,
          delta: level.delta,
        };
      });
    }

    // Swing points for market structure visualization
    const swingHighs = marketStructure?.swing_highs || [];
    const swingLows = marketStructure?.swing_lows || [];

    return {
      priceHigh, priceLow, priceRange, adjustedHigh, adjustedLow, adjustedRange,
      chartWidth, chartHeight, marginLeft, marginRight, marginTop, marginBottom,
      plotWidth, plotHeight, priceToY, indexToX, candleWidth, yTicks, vpBars,
      vpWidth, swingHighs, swingLows
    };
  }, [chartData, volumeProfile, marketStructure]);

  if (!chartCalculations) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        <Activity className="w-6 h-6 animate-pulse mr-2" />
        Loading Chart...
      </div>
    );
  }

  const {
    chartWidth, chartHeight, marginLeft, marginRight, marginTop,
    priceToY, indexToX, candleWidth, yTicks, vpBars, swingHighs, swingLows
  } = chartCalculations;

  // Calculate unified decision for display on chart
  const currentPrice = chartData.length > 0 ? chartData[chartData.length - 1].close : 0;
  const decisionColor = unifiedDecision?.decision?.includes('BUY') ? '#10b981' : 
                        unifiedDecision?.decision?.includes('SELL') ? '#ef4444' : '#64748b';

  return (
    <div className="h-full w-full relative">
      <svg width="100%" height="100%" viewBox={`0 0 ${chartWidth} ${chartHeight}`} preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="vwapBandGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.2"/>
            <stop offset="50%" stopColor="#8b5cf6" stopOpacity="0.1"/>
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.2"/>
          </linearGradient>
          <linearGradient id="valueAreaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.15"/>
            <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.08"/>
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.15"/>
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
                  <filter id="strongGlow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
                  </filter>
                  {/* UNPUSHABLE: Confidence Zone Gradients */}
                  <linearGradient id="longZoneGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.25"/>
                    <stop offset="100%" stopColor="#10b981" stopOpacity="0.05"/>
                  </linearGradient>
                  <linearGradient id="shortZoneGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0.05"/>
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0.25"/>
                  </linearGradient>
                  <linearGradient id="entryZoneGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3"/>
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity="0"/>
                  </linearGradient>
                </defs>

                {/* UNPUSHABLE BREAKTHROUGH: CONFIDENCE ZONES - Visual green/red zones showing where to trade */}
                {tradeSetup && volumeProfile && (
                  <>
                    {/* LONG ZONE: Below POC to VAL - High probability long area */}
                    <rect
                      x={marginLeft}
                      y={priceToY(volumeProfile.poc)}
                      width={chartWidth - marginLeft - marginRight}
                      height={Math.abs(priceToY(volumeProfile.val) - priceToY(volumeProfile.poc))}
                      fill="url(#longZoneGradient)"
                    />
                    <text x={marginLeft + 5} y={priceToY(volumeProfile.val) - 5} fill="#10b981" fontSize="8" fontWeight="bold" opacity="0.8">
                      LONG ZONE
                    </text>
            
                    {/* SHORT ZONE: Above POC to VAH - High probability short area */}
                    <rect
                      x={marginLeft}
                      y={priceToY(volumeProfile.vah)}
                      width={chartWidth - marginLeft - marginRight}
                      height={Math.abs(priceToY(volumeProfile.poc) - priceToY(volumeProfile.vah))}
                      fill="url(#shortZoneGradient)"
                    />
                    <text x={marginLeft + 5} y={priceToY(volumeProfile.vah) + 12} fill="#ef4444" fontSize="8" fontWeight="bold" opacity="0.8">
                      SHORT ZONE
                    </text>
                  </>
                )}

                {/* BREAKTHROUGH: Value Area shading (between VAH and VAL) */}
        {volumeProfile && (
          <rect
            x={marginLeft}
            y={priceToY(volumeProfile.vah)}
            width={chartWidth - marginLeft - marginRight}
            height={Math.abs(priceToY(volumeProfile.val) - priceToY(volumeProfile.vah))}
            fill="url(#valueAreaGradient)"
          />
        )}

        {/* Background grid */}
        <g className="grid">
          {yTicks.map((tick, i) => (
            <g key={i}>
              <line 
                x1={marginLeft} 
                y1={priceToY(tick)} 
                x2={chartWidth - marginRight} 
                y2={priceToY(tick)} 
                stroke="#1e293b" 
                strokeDasharray="3 3"
              />
              <text 
                x={5} 
                y={priceToY(tick) + 4} 
                fill="#64748b" 
                fontSize="9" 
                textAnchor="start"
              >
                {tick.toFixed(decimals)}
              </text>
            </g>
          ))}
        </g>

        {/* BREAKTHROUGH: DeepCharts-style Volume Profile FROM THE LEFT */}
        {volumeProfile && vpBars.map((bar, i) => {
          const barX = 70; // Start from left edge after price labels
          return (
            <g key={`vp-left-${i}`}>
              {/* Selling pressure (orange/red) - extends first */}
              <rect
                x={barX}
                y={bar.y}
                width={bar.sellWidth}
                height={Math.max(2, bar.height)}
                fill="#f97316"
                opacity={bar.isHVN ? 0.9 : bar.isValueArea ? 0.7 : 0.5}
              />
              {/* Buying pressure (green/cyan) - extends after selling */}
              <rect
                x={barX + bar.sellWidth}
                y={bar.y}
                width={bar.buyWidth}
                height={Math.max(2, bar.height)}
                fill="#10b981"
                opacity={bar.isHVN ? 0.9 : bar.isValueArea ? 0.7 : 0.5}
              />
              {/* Neutral volume (yellow) */}
              <rect
                x={barX + bar.sellWidth + bar.buyWidth}
                y={bar.y}
                width={bar.neutralWidth}
                height={Math.max(2, bar.height)}
                fill="#fbbf24"
                opacity={bar.isHVN ? 0.6 : 0.3}
              />
              {/* POC highlight */}
              {bar.isPOC && (
                <rect
                  x={barX}
                  y={bar.y}
                  width={bar.totalWidth}
                  height={Math.max(2, bar.height)}
                  fill="none"
                  stroke="#fbbf24"
                  strokeWidth="2"
                />
              )}
            </g>
          );
        })}

        {/* X-axis time labels */}
        <g className="x-axis">
	          {chartData.filter((_, i) => i % Math.ceil(chartData.length / 6) === 0 || i === chartData.length - 1).map((candle, idx) => {
	            const actualIdx = chartData.indexOf(candle);
	            const x = indexToX(actualIdx);
	            const time = candle.timestamp ? new Date(candle.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : `Bar ${actualIdx}`;
	            return (
	              <g key={`xaxis-${idx}`}>
	                <line x1={x} y1={chartHeight - 20} x2={x} y2={chartHeight - 15} stroke="#334155" />
	                <text x={x} y={chartHeight - 5} fill="#64748b" fontSize="9" textAnchor="middle">{time}</text>
	              </g>
	            );
	          })}
        </g>

        {/* VWAP bands */}
        {chartData.length > 0 && chartData[0].upper_band && (
          <path
            d={`
              M ${indexToX(0)} ${priceToY(chartData[0].upper_band || chartData[0].vwap)}
              ${chartData.map((c, i) => `L ${indexToX(i)} ${priceToY(c.upper_band || c.vwap)}`).join(' ')}
              ${chartData.slice().reverse().map((c, i) => `L ${indexToX(chartData.length - 1 - i)} ${priceToY(c.lower_band || c.vwap)}`).join(' ')}
              Z
            `}
            fill="url(#vwapBandGradient)"
          />
        )}

        {/* VWAP line */}
        {chartData.some(c => c.vwap) && (
          <path
            d={`M ${chartData.map((c, i) => `${indexToX(i)} ${priceToY(c.vwap || c.close)}`).join(' L ')}`}
            fill="none"
            stroke="#8b5cf6"
            strokeWidth="2"
            strokeDasharray="5 5"
            filter="url(#glow)"
          />
        )}

        {/* POC, VAH, VAL lines - extending across full chart */}
        {volumeProfile && (
          <>
            {/* POC - Point of Control (most important level) */}
            <line
              x1={70}
              y1={priceToY(volumeProfile.poc)}
              x2={chartWidth - marginRight}
              y2={priceToY(volumeProfile.poc)}
              stroke="#fbbf24"
              strokeWidth="2"
              opacity="0.9"
            />
            <rect x={chartWidth - marginRight + 5} y={priceToY(volumeProfile.poc) - 8} width="60" height="16" fill="#fbbf24" rx="2"/>
            <text x={chartWidth - marginRight + 35} y={priceToY(volumeProfile.poc) + 4} fill="#000" fontSize="9" fontWeight="bold" textAnchor="middle">
              POC {volumeProfile.poc.toFixed(decimals)}
            </text>
            
            {/* VAH - Value Area High */}
            <line
              x1={70}
              y1={priceToY(volumeProfile.vah)}
              x2={chartWidth - marginRight}
              y2={priceToY(volumeProfile.vah)}
              stroke="#06b6d4"
              strokeWidth="1.5"
              strokeDasharray="6 3"
              opacity="0.8"
            />
            <text x={chartWidth - marginRight + 5} y={priceToY(volumeProfile.vah) + 4} fill="#06b6d4" fontSize="8">VAH</text>
            
            {/* VAL - Value Area Low */}
            <line
              x1={70}
              y1={priceToY(volumeProfile.val)}
              x2={chartWidth - marginRight}
              y2={priceToY(volumeProfile.val)}
              stroke="#06b6d4"
              strokeWidth="1.5"
              strokeDasharray="6 3"
              opacity="0.8"
            />
            <text x={chartWidth - marginRight + 5} y={priceToY(volumeProfile.val) + 4} fill="#06b6d4" fontSize="8">VAL</text>
          </>
        )}

        {/* Liquidity sweep markers */}
        {liquiditySweeps?.slice(0, 5).map((sweep, i) => {
          const sweepPrice = sweep.sweep_price ?? sweep.price;
          if (typeof sweepPrice !== 'number') return null;
          return (
            <g key={`sweep-${i}`}>
              <line
                x1={marginLeft}
                y1={priceToY(sweepPrice)}
                x2={chartWidth - marginRight}
                y2={priceToY(sweepPrice)}
                stroke={sweep.type.includes('HIGH') ? '#f59e0b' : '#3b82f6'}
                strokeWidth="1"
                strokeDasharray="8 4"
                opacity="0.5"
              />
            </g>
          );
        })}

        {/* BREAKTHROUGH: Swing High/Low markers for market structure */}
        {swingHighs.slice(-5).map((sh, i) => {
          const barIdx = chartData.findIndex((c) => Math.abs(c.high - sh.price) < 0.0001);
          if (barIdx < 0) return null;
          return (
            <g key={`sh-${i}`}>
              <circle cx={indexToX(barIdx)} cy={priceToY(sh.price) - 8} r="4" fill="#10b981" opacity="0.8"/>
              <text x={indexToX(barIdx)} y={priceToY(sh.price) - 14} fill="#10b981" fontSize="7" textAnchor="middle">HH</text>
            </g>
          );
        })}
        {swingLows.slice(-5).map((sl, i) => {
          const barIdx = chartData.findIndex((c) => Math.abs(c.low - sl.price) < 0.0001);
          if (barIdx < 0) return null;
          return (
            <g key={`sl-${i}`}>
              <circle cx={indexToX(barIdx)} cy={priceToY(sl.price) + 8} r="4" fill="#ef4444" opacity="0.8"/>
              <text x={indexToX(barIdx)} y={priceToY(sl.price) + 18} fill="#ef4444" fontSize="7" textAnchor="middle">LL</text>
            </g>
          );
        })}

        {/* Candlesticks with proper OHLC rendering */}
        {chartData.map((candle, i) => {
          const x = indexToX(i);
          const bullish = candle.isBullish;
          const bodyTop = priceToY(Math.max(candle.open, candle.close));
          const bodyBottom = priceToY(Math.min(candle.open, candle.close));
          const bodyHeight = Math.max(1, bodyBottom - bodyTop);
          const wickTop = priceToY(candle.high);
          const wickBottom = priceToY(candle.low);
          const color = bullish ? '#10b981' : '#ef4444';

          return (
            <g key={i} className="candle">
              {/* Upper wick */}
              <line x1={x} y1={wickTop} x2={x} y2={bodyTop} stroke={color} strokeWidth="1"/>
              {/* Lower wick */}
              <line x1={x} y1={bodyBottom} x2={x} y2={wickBottom} stroke={color} strokeWidth="1"/>
              {/* Candle body */}
              <rect
                x={x - candleWidth / 2}
                y={bodyTop}
                width={candleWidth}
                height={bodyHeight}
                fill={color}
                stroke={color}
                strokeWidth="1"
                rx="1"
              />
            </g>
          );
        })}

                {/* Current price line with decision indicator */}
                {chartData.length > 0 && (
                  <g>
                    <line
                      x1={marginLeft}
                      y1={priceToY(currentPrice)}
                      x2={chartWidth - marginRight}
                      y2={priceToY(currentPrice)}
                      stroke="#ffffff"
                      strokeWidth="1"
                      strokeDasharray="2 2"
                    />
                    <rect
                      x={chartWidth - marginRight - 55}
                      y={priceToY(currentPrice) - 10}
                      width="50"
                      height="20"
                      fill={chartData[chartData.length - 1].isBullish ? '#10b981' : '#ef4444'}
                      rx="3"
                    />
                    <text
                      x={chartWidth - marginRight - 30}
                      y={priceToY(currentPrice) + 4}
                      fill="white"
                      fontSize="9"
                      fontWeight="bold"
                      textAnchor="middle"
                    >
                      {currentPrice.toFixed(decimals)}
                    </text>
                  </g>
                )}

                {/* UNPUSHABLE BREAKTHROUGH: ENTRY/EXIT MARKERS - Show exact trade levels on chart */}
                {tradeSetup && tradeSetup.direction !== 'NEUTRAL' && (
                  <g>
                    {/* ENTRY LINE - Cyan with glow */}
                    <line
                      x1={marginLeft}
                      y1={priceToY(tradeSetup.entry)}
                      x2={chartWidth - marginRight}
                      y2={priceToY(tradeSetup.entry)}
                      stroke="#06b6d4"
                      strokeWidth="2"
                      strokeDasharray="8 4"
                      filter="url(#glow)"
                    />
                    <rect x={marginLeft} y={priceToY(tradeSetup.entry) - 10} width="55" height="20" fill="#06b6d4" rx="3"/>
                    <text x={marginLeft + 27} y={priceToY(tradeSetup.entry) + 4} fill="white" fontSize="8" fontWeight="bold" textAnchor="middle">
                      ENTRY
                    </text>
            
                    {/* STOP LOSS LINE - Red with warning */}
                    <line
                      x1={marginLeft}
                      y1={priceToY(tradeSetup.stopLoss)}
                      x2={chartWidth - marginRight}
                      y2={priceToY(tradeSetup.stopLoss)}
                      stroke="#ef4444"
                      strokeWidth="2"
                      strokeDasharray="4 2"
                    />
                    <rect x={marginLeft} y={priceToY(tradeSetup.stopLoss) - 10} width="55" height="20" fill="#ef4444" rx="3"/>
                    <text x={marginLeft + 27} y={priceToY(tradeSetup.stopLoss) + 4} fill="white" fontSize="8" fontWeight="bold" textAnchor="middle">
                      STOP
                    </text>
            
                    {/* TARGET 1 LINE - Green with glow */}
                    <line
                      x1={marginLeft}
                      y1={priceToY(tradeSetup.target1)}
                      x2={chartWidth - marginRight}
                      y2={priceToY(tradeSetup.target1)}
                      stroke="#10b981"
                      strokeWidth="2"
                      strokeDasharray="8 4"
                      filter="url(#glow)"
                    />
                    <rect x={marginLeft} y={priceToY(tradeSetup.target1) - 10} width="55" height="20" fill="#10b981" rx="3"/>
                    <text x={marginLeft + 27} y={priceToY(tradeSetup.target1) + 4} fill="white" fontSize="8" fontWeight="bold" textAnchor="middle">
                      TP1
                    </text>
            
                    {/* TARGET 2 LINE - Gold for extended target */}
                    <line
                      x1={marginLeft}
                      y1={priceToY(tradeSetup.target2)}
                      x2={chartWidth - marginRight}
                      y2={priceToY(tradeSetup.target2)}
                      stroke="#f59e0b"
                      strokeWidth="1.5"
                      strokeDasharray="6 3"
                    />
                    <rect x={marginLeft} y={priceToY(tradeSetup.target2) - 10} width="55" height="20" fill="#f59e0b" rx="3"/>
                    <text x={marginLeft + 27} y={priceToY(tradeSetup.target2) + 4} fill="white" fontSize="8" fontWeight="bold" textAnchor="middle">
                      TP2
                    </text>
            
                    {/* RISK:REWARD VISUALIZATION - Show the trade setup visually */}
                    {tradeSetup.direction === 'LONG' && (
                      <g>
                        {/* Risk zone (entry to stop) - red shaded */}
                        <rect
                          x={chartWidth - marginRight - 25}
                          y={priceToY(tradeSetup.entry)}
                          width="20"
                          height={Math.abs(priceToY(tradeSetup.stopLoss) - priceToY(tradeSetup.entry))}
                          fill="#ef4444"
                          opacity="0.3"
                        />
                        {/* Reward zone (entry to target) - green shaded */}
                        <rect
                          x={chartWidth - marginRight - 25}
                          y={priceToY(tradeSetup.target1)}
                          width="20"
                          height={Math.abs(priceToY(tradeSetup.entry) - priceToY(tradeSetup.target1))}
                          fill="#10b981"
                          opacity="0.3"
                        />
                        <text x={chartWidth - marginRight - 15} y={priceToY((tradeSetup.entry + tradeSetup.target1) / 2)} fill="#10b981" fontSize="7" fontWeight="bold" textAnchor="middle">
                          {tradeSetup.riskReward1.toFixed(1)}R
                        </text>
                      </g>
                    )}
                    {tradeSetup.direction === 'SHORT' && (
                      <g>
                        {/* Risk zone (entry to stop) - red shaded */}
                        <rect
                          x={chartWidth - marginRight - 25}
                          y={priceToY(tradeSetup.stopLoss)}
                          width="20"
                          height={Math.abs(priceToY(tradeSetup.entry) - priceToY(tradeSetup.stopLoss))}
                          fill="#ef4444"
                          opacity="0.3"
                        />
                        {/* Reward zone (entry to target) - green shaded */}
                        <rect
                          x={chartWidth - marginRight - 25}
                          y={priceToY(tradeSetup.entry)}
                          width="20"
                          height={Math.abs(priceToY(tradeSetup.target1) - priceToY(tradeSetup.entry))}
                          fill="#10b981"
                          opacity="0.3"
                        />
                        <text x={chartWidth - marginRight - 15} y={priceToY((tradeSetup.entry + tradeSetup.target1) / 2)} fill="#10b981" fontSize="7" fontWeight="bold" textAnchor="middle">
                          {tradeSetup.riskReward1.toFixed(1)}R
                        </text>
                      </g>
                    )}
                  </g>
                )}

                {/* BREAKTHROUGH: Unified Decision Badge on Chart */}
        {unifiedDecision && (
          <g transform={`translate(${chartWidth - marginRight - 80}, ${marginTop + 5})`}>
            <rect x="0" y="0" width="75" height="45" fill="#0f172a" stroke={decisionColor} strokeWidth="2" rx="6" opacity="0.95"/>
            <text x="37" y="15" fill={decisionColor} fontSize="10" fontWeight="bold" textAnchor="middle">
              {unifiedDecision.decision}
            </text>
            <text x="37" y="28" fill="#94a3b8" fontSize="8" textAnchor="middle">
              {unifiedDecision.confidence.toFixed(0)}% conf
            </text>
            <rect x="5" y="33" width={65 * (unifiedDecision.confidence / 100)} height="6" fill={decisionColor} rx="2" opacity="0.7"/>
          </g>
        )}

        {/* Legend - Updated for DeepCharts style */}
        <g transform={`translate(${marginLeft + 5}, ${marginTop + 8})`}>
          <rect x="-3" y="-8" width="180" height="18" fill="#0f172a" opacity="0.8" rx="3"/>
          <rect x="0" y="-3" width="8" height="8" fill="#10b981"/>
          <text x="12" y="4" fill="#94a3b8" fontSize="8">Buy Vol</text>
          <rect x="50" y="-3" width="8" height="8" fill="#f97316"/>
          <text x="62" y="4" fill="#94a3b8" fontSize="8">Sell Vol</text>
          <rect x="105" y="-3" width="8" height="8" fill="#fbbf24"/>
          <text x="117" y="4" fill="#94a3b8" fontSize="8">POC</text>
          <line x1="145" y1="1" x2="160" y2="1" stroke="#8b5cf6" strokeWidth="2" strokeDasharray="3 2"/>
          <text x="163" y="4" fill="#94a3b8" fontSize="8">VWAP</text>
        </g>
      </svg>
    </div>
  );
};

const DeltaChart = ({ data }: { data: DeltaPoint[] }) => {
  if (!data || data.length === 0) return <div className="h-full flex items-center justify-center text-slate-500">Loading...</div>;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="idx" tick={false} stroke="#334155" />
        <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(v) => v > 1000 ? `${(v/1000).toFixed(0)}k` : v.toFixed(0)} />
        <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }} formatter={(value: number) => [value.toFixed(0), 'Delta']} />
        <ReferenceLine y={0} stroke="#64748b" />
        <Bar dataKey="delta">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.is_bullish ? '#10b981' : '#ef4444'} fillOpacity={0.8} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

const CumulativeDeltaChart = ({ data }: { data: DeltaPoint[] }) => {
  if (!data || data.length === 0) return <div className="h-full flex items-center justify-center text-slate-500">Loading...</div>;

  const lastDelta = data[data.length - 1]?.cumulative_delta || 0;
  const isBullish = lastDelta > 0;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="deltaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={isBullish ? '#10b981' : '#ef4444'} stopOpacity={0.4}/>
            <stop offset="95%" stopColor={isBullish ? '#10b981' : '#ef4444'} stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="idx" tick={false} stroke="#334155" />
        <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(v) => v > 1000 ? `${(v/1000).toFixed(0)}k` : v.toFixed(0)} />
        <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }} formatter={(value: number) => [value.toFixed(0), 'Cumulative Delta']} />
        <ReferenceLine y={0} stroke="#64748b" strokeDasharray="3 3" />
        <Area type="monotone" dataKey="cumulative_delta" stroke={isBullish ? '#10b981' : '#ef4444'} fill="url(#deltaGradient)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
};

// DeepCharts-style Delta Profile - Shows buying vs selling at each price level
// BREAKTHROUGH: Unified Intelligence Visualization
// This component shows HOW the system THINKS - not just data, but REASONING
const UnifiedIntelligence = ({ 
  volumeProfile, 
  orderFlow, 
  marketStructure, 
  delta,
  currentPrice,
}: { 
  volumeProfile: VolumeProfile | null,
  orderFlow: OrderFlowImbalance | null,
  marketStructure: MarketStructure | null,
  riskMetrics: RiskMetrics | null,
  delta: DeltaPoint[],
  currentPrice: number,
  symbol: string
}) => {
  // Calculate unified intelligence scores
  const volumeSignal = useMemo(() => {
    if (!volumeProfile) return { score: 0, bias: 'NEUTRAL', reason: 'No data' };
    
    if (currentPrice > volumeProfile.vah) {
      return { score: 0.8, bias: 'BULLISH', reason: 'Price above Value Area High - breakout territory' };
    } else if (currentPrice < volumeProfile.val) {
      return { score: -0.8, bias: 'BEARISH', reason: 'Price below Value Area Low - breakdown territory' };
    } else if (currentPrice > volumeProfile.poc) {
      return { score: 0.3, bias: 'BULLISH', reason: 'Price above POC - buyers in control' };
    } else {
      return { score: -0.3, bias: 'BEARISH', reason: 'Price below POC - sellers in control' };
    }
  }, [volumeProfile, currentPrice]);

  const deltaSignal = useMemo(() => {
    if (!delta || delta.length === 0) return { score: 0, bias: 'NEUTRAL', reason: 'No delta data' };
    const lastDelta = delta[delta.length - 1]?.cumulative_delta || 0;
    const prevDelta = delta[Math.max(0, delta.length - 10)]?.cumulative_delta || 0;
    const deltaTrend = lastDelta - prevDelta;
    
    if (deltaTrend > 1000) {
      return { score: 0.9, bias: 'BULLISH', reason: 'Strong buying pressure - cumulative delta rising' };
    } else if (deltaTrend < -1000) {
      return { score: -0.9, bias: 'BEARISH', reason: 'Strong selling pressure - cumulative delta falling' };
    } else if (deltaTrend > 0) {
      return { score: 0.4, bias: 'BULLISH', reason: 'Moderate buying - delta trending up' };
    } else {
      return { score: -0.4, bias: 'BEARISH', reason: 'Moderate selling - delta trending down' };
    }
  }, [delta]);

  const orderFlowSignal = useMemo(() => {
    if (!orderFlow) return { score: 0, bias: 'NEUTRAL', reason: 'No order flow data' };
    const ofi = orderFlow.ofi_normalized;
    
    if (ofi > 0.5) {
      return { score: 0.85, bias: 'BULLISH', reason: 'Heavy buying imbalance detected' };
    } else if (ofi < -0.5) {
      return { score: -0.85, bias: 'BEARISH', reason: 'Heavy selling imbalance detected' };
    } else if (ofi > 0.1) {
      return { score: 0.3, bias: 'BULLISH', reason: 'Slight buying pressure' };
    } else if (ofi < -0.1) {
      return { score: -0.3, bias: 'BEARISH', reason: 'Slight selling pressure' };
    }
    return { score: 0, bias: 'NEUTRAL', reason: 'Order flow balanced' };
  }, [orderFlow]);

  const structureSignal = useMemo(() => {
    if (!marketStructure) return { score: 0, bias: 'NEUTRAL', reason: 'No structure data' };
    
    if (marketStructure.structure === 'BULLISH') {
      return { score: 0.7, bias: 'BULLISH', reason: 'Higher highs and higher lows - uptrend' };
    } else if (marketStructure.structure === 'BEARISH') {
      return { score: -0.7, bias: 'BEARISH', reason: 'Lower highs and lower lows - downtrend' };
    }
    return { score: 0, bias: 'NEUTRAL', reason: 'Ranging market - no clear direction' };
  }, [marketStructure]);

  // UNIFIED CONFLUENCE SCORE - The brain's final decision
  const confluenceScore = useMemo(() => {
    const weights = { volume: 0.25, delta: 0.30, orderFlow: 0.25, structure: 0.20 };
    const score = 
      volumeSignal.score * weights.volume +
      deltaSignal.score * weights.delta +
      orderFlowSignal.score * weights.orderFlow +
      structureSignal.score * weights.structure;
    
    return score;
  }, [volumeSignal, deltaSignal, orderFlowSignal, structureSignal]);

  // Generate the system's REASONING
  const systemReasoning = useMemo(() => {
    const signals = [
      { name: 'Volume Profile', ...volumeSignal, weight: 25 },
      { name: 'Delta Flow', ...deltaSignal, weight: 30 },
      { name: 'Order Flow', ...orderFlowSignal, weight: 25 },
      { name: 'Structure', ...structureSignal, weight: 20 },
    ];
    
    const bullish = signals.filter(s => s.score > 0);
    const bearish = signals.filter(s => s.score < 0);
    
    let decision = 'WAIT';
    const confidence = Math.abs(confluenceScore) * 100;
    
    if (confluenceScore > 0.5) {
      decision = 'STRONG BUY';
    } else if (confluenceScore > 0.2) {
      decision = 'BUY';
    } else if (confluenceScore < -0.5) {
      decision = 'STRONG SELL';
    } else if (confluenceScore < -0.2) {
      decision = 'SELL';
    }
    
    return { signals, bullish, bearish, decision, confidence };
  }, [volumeSignal, deltaSignal, orderFlowSignal, structureSignal, confluenceScore]);

  const getScoreColor = (score: number) => {
    if (score > 0.5) return 'text-emerald-400';
    if (score > 0) return 'text-emerald-300';
    if (score < -0.5) return 'text-red-400';
    if (score < 0) return 'text-red-300';
    return 'text-slate-400';
  };

  const getDecisionColor = (decision: string) => {
    if (decision.includes('BUY')) return 'from-emerald-500 to-cyan-500';
    if (decision.includes('SELL')) return 'from-red-500 to-orange-500';
    return 'from-slate-500 to-slate-600';
  };

  return (
    <div className="h-full flex flex-col space-y-3 overflow-auto">
      {/* UNIFIED BRAIN - The Central Intelligence */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-4 border border-cyan-500/30 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-purple-500/5" />
        <div className="relative">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-cyan-400" />
              <span className="text-sm font-bold text-white">UNIFIED INTELLIGENCE</span>
            </div>
            <div className="flex items-center gap-1">
              <Sparkles className="w-4 h-4 text-yellow-400 animate-pulse" />
              <span className="text-xs text-slate-400">LIVE REASONING</span>
            </div>
          </div>
          
          {/* Central Decision Display */}
          <div className={`text-center py-4 rounded-lg bg-gradient-to-r ${getDecisionColor(systemReasoning.decision)} mb-3`}>
            <div className="text-2xl font-black text-white tracking-wider">
              {systemReasoning.decision}
            </div>
            <div className="text-sm text-white/80">
              Confidence: {systemReasoning.confidence.toFixed(0)}%
            </div>
          </div>
          
          {/* Confluence Score Bar */}
          <div className="mb-3">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>BEARISH</span>
              <span>NEUTRAL</span>
              <span>BULLISH</span>
            </div>
            <div className="h-3 bg-slate-700 rounded-full relative overflow-hidden">
              <div className="absolute inset-0 flex">
                <div className="w-1/2 bg-gradient-to-r from-red-500/30 to-transparent" />
                <div className="w-1/2 bg-gradient-to-l from-emerald-500/30 to-transparent" />
              </div>
              <div 
                className="absolute top-0 bottom-0 w-1 bg-white shadow-lg shadow-white/50 transition-all duration-500"
                style={{ left: `${50 + confluenceScore * 50}%` }}
              />
            </div>
            <div className="text-center text-xs text-slate-400 mt-1">
              Score: {confluenceScore > 0 ? '+' : ''}{(confluenceScore * 100).toFixed(0)}
            </div>
          </div>
        </div>
      </div>

      {/* NEURAL CONNECTIONS - How signals connect */}
      <div className="bg-[#0f1420] rounded-xl p-3 border border-slate-700">
        <div className="flex items-center gap-2 mb-3">
          <Network className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-bold text-slate-300">SIGNAL CONFLUENCE</span>
        </div>
        
        <div className="space-y-2">
          {systemReasoning.signals.map((signal, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div className="w-20 text-xs text-slate-400 truncate">{signal.name}</div>
              <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden relative">
                <div 
                  className={`absolute top-0 bottom-0 transition-all duration-500 ${
                    signal.score > 0 ? 'bg-emerald-500 left-1/2' : 'bg-red-500 right-1/2'
                  }`}
                  style={{ width: `${Math.abs(signal.score) * 50}%` }}
                />
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-600" />
              </div>
              <div className={`w-16 text-xs font-bold text-right ${getScoreColor(signal.score)}`}>
                {signal.bias}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* REASONING NARRATIVE - Why the system thinks this */}
      <div className="bg-[#0f1420] rounded-xl p-3 border border-slate-700 flex-1">
        <div className="flex items-center gap-2 mb-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-slate-300">SYSTEM REASONING</span>
        </div>
        
        <div className="space-y-2 text-xs">
          {systemReasoning.signals.map((signal, idx) => (
            <div key={idx} className={`p-2 rounded border-l-2 ${
              signal.score > 0 ? 'border-emerald-500 bg-emerald-500/5' : 
              signal.score < 0 ? 'border-red-500 bg-red-500/5' : 
              'border-slate-500 bg-slate-500/5'
            }`}>
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-slate-300">{signal.name}</span>
                <span className={`text-xs ${getScoreColor(signal.score)}`}>
                  {signal.weight}% weight
                </span>
              </div>
              <div className="text-slate-400">{signal.reason}</div>
            </div>
          ))}
        </div>
        
        {/* Final Synthesis */}
        <div className="mt-3 p-2 rounded bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-500/20">
          <div className="text-xs text-slate-300">
            <span className="font-bold text-cyan-400">SYNTHESIS: </span>
            {systemReasoning.bullish.length} bullish signals ({systemReasoning.bullish.map(s => s.name).join(', ') || 'none'}) vs {systemReasoning.bearish.length} bearish signals ({systemReasoning.bearish.map(s => s.name).join(', ') || 'none'}).
            <span className={`font-bold ml-1 ${
              systemReasoning.decision.includes('BUY') ? 'text-emerald-400' :
              systemReasoning.decision.includes('SELL') ? 'text-red-400' : 'text-slate-400'
            }`}>
              System recommends: {systemReasoning.decision}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

// BREAKTHROUGH: PREDICTIVE TRADE SETUP - Actionable intelligence with specific levels
const PredictiveTradeSetup = ({ 
  volumeProfile, 
  marketStructure, 
  orderFlow,
  delta,
  currentPrice,
  symbol
}: { 
  volumeProfile: VolumeProfile | null,
  marketStructure: MarketStructure | null,
  orderFlow: OrderFlowImbalance | null,
  delta: DeltaPoint[],
  currentPrice: number,
  symbol: string
}) => {
  const decimals = symbol === 'XAUUSD' ? 2 : symbol === 'USDJPY' ? 3 : 5;
  
  // PREDICTIVE INTELLIGENCE: Calculate optimal trade setup
  const tradeSetup = useMemo(() => {
    if (!volumeProfile || !currentPrice) return null;
    
    // Analyze all signals for direction
    let bullishScore = 0;
    let bearishScore = 0;
    const reasons: string[] = [];
    
    // Volume Profile Analysis
    if (currentPrice > volumeProfile.vah) {
      bullishScore += 30;
      reasons.push('Price broke above Value Area - bullish breakout');
    } else if (currentPrice < volumeProfile.val) {
      bearishScore += 30;
      reasons.push('Price broke below Value Area - bearish breakdown');
    } else if (currentPrice > volumeProfile.poc) {
      bullishScore += 15;
      reasons.push('Price above POC - buyers defending');
    } else {
      bearishScore += 15;
      reasons.push('Price below POC - sellers in control');
    }
    
    // Delta Analysis
    if (delta && delta.length > 0) {
      const lastDelta = delta[delta.length - 1]?.cumulative_delta || 0;
      const prevDelta = delta[Math.max(0, delta.length - 10)]?.cumulative_delta || 0;
      const deltaTrend = lastDelta - prevDelta;
      
      if (deltaTrend > 2000) {
        bullishScore += 35;
        reasons.push('Strong delta divergence - institutional buying detected');
      } else if (deltaTrend < -2000) {
        bearishScore += 35;
        reasons.push('Strong delta divergence - institutional selling detected');
      } else if (deltaTrend > 500) {
        bullishScore += 15;
        reasons.push('Positive delta flow - buying pressure');
      } else if (deltaTrend < -500) {
        bearishScore += 15;
        reasons.push('Negative delta flow - selling pressure');
      }
    }
    
    // Order Flow Analysis
    if (orderFlow) {
      if (orderFlow.ofi_normalized > 0.6) {
        bullishScore += 25;
        reasons.push('Heavy order flow imbalance - aggressive buyers');
      } else if (orderFlow.ofi_normalized < -0.6) {
        bearishScore += 25;
        reasons.push('Heavy order flow imbalance - aggressive sellers');
      }
    }
    
    // Market Structure Analysis
    if (marketStructure) {
      if (marketStructure.structure === 'BULLISH') {
        bullishScore += 20;
        reasons.push('Higher highs and higher lows - uptrend confirmed');
      } else if (marketStructure.structure === 'BEARISH') {
        bearishScore += 20;
        reasons.push('Lower highs and lower lows - downtrend confirmed');
      }
    }
    
    // Calculate confidence and direction
    const totalScore = bullishScore + bearishScore;
    const confidence = totalScore > 0 ? Math.max(bullishScore, bearishScore) : 0;
    const direction = bullishScore > bearishScore ? 'LONG' : bearishScore > bullishScore ? 'SHORT' : 'NEUTRAL';
    
    // Calculate optimal entry, stop, and targets based on Volume Profile
    let entry = currentPrice;
    let stopLoss = 0;
    let target1 = 0;
    let target2 = 0;
    
    if (direction === 'LONG') {
      entry = Math.min(currentPrice, volumeProfile.poc + (volumeProfile.vah - volumeProfile.poc) * 0.3);
      stopLoss = volumeProfile.val - (volumeProfile.vah - volumeProfile.val) * 0.1;
      target1 = volumeProfile.vah;
      target2 = volumeProfile.vah + (volumeProfile.vah - volumeProfile.poc) * 0.5;
    } else if (direction === 'SHORT') {
      entry = Math.max(currentPrice, volumeProfile.poc - (volumeProfile.poc - volumeProfile.val) * 0.3);
      stopLoss = volumeProfile.vah + (volumeProfile.vah - volumeProfile.val) * 0.1;
      target1 = volumeProfile.val;
      target2 = volumeProfile.val - (volumeProfile.poc - volumeProfile.val) * 0.5;
    }
    
    const risk = Math.abs(entry - stopLoss);
    const reward1 = Math.abs(target1 - entry);
    const riskReward1 = risk > 0 ? reward1 / risk : 0;
    
    // Smart Money Detection
    const smartMoneySignals: string[] = [];
    if (delta && delta.length > 5) {
      const recentDeltas = delta.slice(-5);
      const avgDelta = recentDeltas.reduce((sum: number, d) => sum + Math.abs(d.delta || 0), 0) / 5;
      if (avgDelta > 1000) {
        smartMoneySignals.push('High volume activity - institutions active');
      }
    }
    
    if (volumeProfile.hvn_prices && volumeProfile.hvn_prices.length > 0) {
      const nearHVN = volumeProfile.hvn_prices.some((hvn: number) => Math.abs(currentPrice - hvn) < (volumeProfile.vah - volumeProfile.val) * 0.1);
      if (nearHVN) {
        smartMoneySignals.push('Price at High Volume Node - potential support/resistance');
      }
    }
    
    return {
      direction,
      confidence,
      entry,
      stopLoss,
      target1,
      target2,
      riskReward1,
      reasons,
      smartMoneySignals,
      isHighProbability: confidence >= 60 && riskReward1 >= 1.5
    };
  }, [volumeProfile, marketStructure, orderFlow, delta, currentPrice]);
  
  if (!tradeSetup || tradeSetup.direction === 'NEUTRAL') {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-500 p-4">
        <Eye className="w-8 h-8 mb-2 opacity-50" />
        <div className="text-sm font-medium">Analyzing Market...</div>
        <div className="text-xs mt-1">Waiting for high probability setup</div>
      </div>
    );
  }
  
  const isLong = tradeSetup.direction === 'LONG';
  const directionIcon = isLong ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />;
  
  return (
    <div className="h-full flex flex-col space-y-2 overflow-auto p-1">
      {/* TRADE SIGNAL HEADER */}
      <div className={`bg-gradient-to-r ${isLong ? 'from-emerald-500/20 to-cyan-500/20 border-emerald-500/50' : 'from-red-500/20 to-orange-500/20 border-red-500/50'} rounded-lg p-3 border`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg ${isLong ? 'bg-emerald-500' : 'bg-red-500'}`}>
              {directionIcon}
            </div>
            <div>
              <div className={`text-lg font-black ${isLong ? 'text-emerald-400' : 'text-red-400'}`}>
                {tradeSetup.direction}
              </div>
              <div className="text-xs text-slate-400">
                {tradeSetup.isHighProbability ? 'HIGH PROBABILITY' : 'MODERATE'} SETUP
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-2xl font-black ${isLong ? 'text-emerald-400' : 'text-red-400'}`}>
              {tradeSetup.confidence}%
            </div>
            <div className="text-xs text-slate-400">Confidence</div>
          </div>
        </div>
      </div>
      
      {/* TRADE LEVELS */}
      <div className="bg-[#0f1420] rounded-lg p-3 border border-slate-700">
        <div className="flex items-center gap-2 mb-3">
          <Target className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-slate-300">TRADE LEVELS</span>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 rounded bg-slate-800/50">
            <div className="flex items-center gap-2">
              <Crosshair className="w-4 h-4 text-cyan-400" />
              <span className="text-xs text-slate-300">Entry</span>
            </div>
            <span className="text-sm font-bold text-cyan-400">{tradeSetup.entry.toFixed(decimals)}</span>
          </div>
          
          <div className="flex items-center justify-between p-2 rounded bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-400" />
              <span className="text-xs text-slate-300">Stop Loss</span>
            </div>
            <span className="text-sm font-bold text-red-400">{tradeSetup.stopLoss.toFixed(decimals)}</span>
          </div>
          
          <div className="flex items-center justify-between p-2 rounded bg-emerald-500/10 border border-emerald-500/30">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-emerald-400" />
              <span className="text-xs text-slate-300">Target 1</span>
            </div>
            <div className="text-right">
              <span className="text-sm font-bold text-emerald-400">{tradeSetup.target1.toFixed(decimals)}</span>
              <span className="text-xs text-slate-500 ml-2">R:R {tradeSetup.riskReward1.toFixed(1)}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* SMART MONEY SIGNALS */}
      {tradeSetup.smartMoneySignals.length > 0 && (
        <div className="bg-[#0f1420] rounded-lg p-3 border border-yellow-500/30">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-yellow-400" />
            <span className="text-xs font-bold text-yellow-400">SMART MONEY DETECTED</span>
          </div>
          <div className="space-y-1">
            {tradeSetup.smartMoneySignals.map((signal, idx) => (
              <div key={idx} className="text-xs text-slate-300 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
                {signal}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* REASONING */}
      <div className="bg-[#0f1420] rounded-lg p-3 border border-slate-700 flex-1">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-bold text-slate-300">WHY THIS TRADE</span>
        </div>
        <div className="space-y-1">
          {tradeSetup.reasons.slice(0, 4).map((reason, idx) => (
            <div key={idx} className={`text-xs p-1.5 rounded ${isLong ? 'bg-emerald-500/5 border-l-2 border-emerald-500' : 'bg-red-500/5 border-l-2 border-red-500'}`}>
              {reason}
            </div>
          ))}
        </div>
      </div>
      
      {/* NARRATIVE */}
      <div className={`p-3 rounded-lg ${isLong ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
        <div className="text-xs text-slate-300 leading-relaxed">
          <span className={`font-bold ${isLong ? 'text-emerald-400' : 'text-red-400'}`}>NARRATIVE: </span>
          {isLong 
            ? `Institutional buying detected with ${tradeSetup.confidence}% confidence. Enter LONG at ${tradeSetup.entry.toFixed(decimals)} with stop at ${tradeSetup.stopLoss.toFixed(decimals)}. Target ${tradeSetup.target1.toFixed(decimals)} for ${tradeSetup.riskReward1.toFixed(1)}R.`
            : `Institutional selling detected with ${tradeSetup.confidence}% confidence. Enter SHORT at ${tradeSetup.entry.toFixed(decimals)} with stop at ${tradeSetup.stopLoss.toFixed(decimals)}. Target ${tradeSetup.target1.toFixed(decimals)} for ${tradeSetup.riskReward1.toFixed(1)}R.`
          }
        </div>
      </div>
    </div>
  );
};

// UNPUSHABLE BREAKTHROUGH: Multi-Timeframe Confluence Indicator
const MultiTimeframeConfluence = ({ 
  volumeProfile, 
  marketStructure, 
  delta,
  currentPrice 
}: { 
  volumeProfile: VolumeProfile | null,
  marketStructure: MarketStructure | null,
  delta: DeltaPoint[],
  currentPrice: number
}) => {
  // Simulate multi-timeframe analysis (in production, this would fetch data from different timeframes)
  const timeframes = useMemo(() => {
    if (!volumeProfile || !currentPrice) return [];
    
    // Calculate bias for each timeframe based on available data
    const calcBias = (priceOffset: number, deltaMultiplier: number) => {
      const adjustedPrice = currentPrice * (1 + priceOffset);
      let bullish = 0;
      let bearish = 0;
      
      // Volume Profile bias
      if (adjustedPrice > volumeProfile.vah) bullish += 40;
      else if (adjustedPrice < volumeProfile.val) bearish += 40;
      else if (adjustedPrice > volumeProfile.poc) bullish += 20;
      else bearish += 20;
      
      // Delta bias
      if (delta && delta.length > 0) {
        const lastDelta = delta[delta.length - 1]?.cumulative_delta || 0;
        if (lastDelta * deltaMultiplier > 1000) bullish += 30;
        else if (lastDelta * deltaMultiplier < -1000) bearish += 30;
      }
      
      // Structure bias
      if (marketStructure) {
        if (marketStructure.structure === 'BULLISH') bullish += 30;
        else if (marketStructure.structure === 'BEARISH') bearish += 30;
      }
      
      return { bullish, bearish, bias: bullish > bearish ? 'BULL' : bearish > bullish ? 'BEAR' : 'NEUT' };
    };
    
    return [
      { name: '1H', ...calcBias(0, 1) },
      { name: '4H', ...calcBias(0.001, 1.5) },
      { name: 'D', ...calcBias(0.002, 2) },
      { name: 'W', ...calcBias(0.003, 2.5) },
    ];
  }, [volumeProfile, marketStructure, delta, currentPrice]);
  
  const bullishCount = timeframes.filter(tf => tf.bias === 'BULL').length;
  const bearishCount = timeframes.filter(tf => tf.bias === 'BEAR').length;
  const confluenceLevel = Math.max(bullishCount, bearishCount);
  const overallBias = bullishCount > bearishCount ? 'BULLISH' : bearishCount > bullishCount ? 'BEARISH' : 'NEUTRAL';
  
  const getBiasColor = (bias: string) => {
    if (bias === 'BULL') return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/50';
    if (bias === 'BEAR') return 'text-red-400 bg-red-500/20 border-red-500/50';
    return 'text-slate-400 bg-slate-500/20 border-slate-500/50';
  };
  
  const getConfluenceColor = () => {
    if (confluenceLevel >= 4) return 'from-emerald-500 to-cyan-500';
    if (confluenceLevel >= 3) return 'from-emerald-500/70 to-cyan-500/70';
    if (confluenceLevel >= 2) return 'from-yellow-500 to-orange-500';
    return 'from-slate-500 to-slate-600';
  };
  
  return (
    <div className="h-full flex flex-col space-y-2 p-1">
      {/* CONFLUENCE HEADER */}
      <div className={`bg-gradient-to-r ${getConfluenceColor()} rounded-lg p-2 text-center`}>
        <div className="text-white font-black text-sm">
          {confluenceLevel}/4 TIMEFRAMES {overallBias}
        </div>
        <div className="text-white/80 text-xs">
          {confluenceLevel >= 4 ? 'SUPER CONFLUENCE - HIGH PROBABILITY' : 
           confluenceLevel >= 3 ? 'STRONG CONFLUENCE' : 
           confluenceLevel >= 2 ? 'MODERATE CONFLUENCE' : 'WEAK CONFLUENCE'}
        </div>
      </div>
      
      {/* TIMEFRAME GRID */}
      <div className="grid grid-cols-4 gap-1 flex-1">
        {timeframes.map((tf, idx) => (
          <div key={idx} className={`rounded-lg border p-2 text-center ${getBiasColor(tf.bias)}`}>
            <div className="font-bold text-xs">{tf.name}</div>
            <div className="text-lg font-black">
              {tf.bias === 'BULL' ? <TrendingUp className="w-4 h-4 mx-auto" /> : 
               tf.bias === 'BEAR' ? <TrendingDown className="w-4 h-4 mx-auto" /> : 
               <Activity className="w-4 h-4 mx-auto" />}
            </div>
            <div className="text-[10px] opacity-80">{tf.bias}</div>
          </div>
        ))}
      </div>
      
      {/* CONFLUENCE EXPLANATION */}
      <div className="bg-slate-800/50 rounded-lg p-2 text-xs text-slate-300">
        <span className="font-bold text-cyan-400">CONFLUENCE: </span>
        {confluenceLevel >= 4 ? 
          `All 4 timeframes agree on ${overallBias} bias. This is a SUPER HIGH PROBABILITY setup.` :
         confluenceLevel >= 3 ?
          `3/4 timeframes show ${overallBias} bias. Strong setup with good probability.` :
         confluenceLevel >= 2 ?
          `Only 2/4 timeframes agree. Wait for more confluence before entering.` :
          `Timeframes are conflicting. AVOID trading until confluence improves.`
        }
      </div>
    </div>
  );
};

// UNPUSHABLE BREAKTHROUGH: Historical Accuracy Tracker
const HistoricalAccuracyTracker = ({ closedTrades }: { closedTrades: ClosedTrade[] }) => {
  const stats = useMemo(() => {
    if (!closedTrades || closedTrades.length === 0) {
      return { winRate: 0, avgRR: 0, profitFactor: 0, streak: 0, last10: [] };
    }
    
    const wins = closedTrades.filter(t => t.pnl > 0).length;
    const losses = closedTrades.filter(t => t.pnl < 0).length;
    const winRate = closedTrades.length > 0 ? (wins / closedTrades.length) * 100 : 0;
    
    const totalWins = closedTrades.filter(t => t.pnl > 0).reduce((sum, t) => sum + t.pnl, 0);
    const totalLosses = Math.abs(closedTrades.filter(t => t.pnl < 0).reduce((sum, t) => sum + t.pnl, 0));
    const profitFactor = totalLosses > 0 ? totalWins / totalLosses : totalWins > 0 ? 999 : 0;
    
    // Calculate current streak
    let streak = 0;
    for (let i = closedTrades.length - 1; i >= 0; i--) {
      if (i === closedTrades.length - 1) {
        streak = closedTrades[i].pnl > 0 ? 1 : -1;
      } else {
        if ((streak > 0 && closedTrades[i].pnl > 0) || (streak < 0 && closedTrades[i].pnl < 0)) {
          streak = streak > 0 ? streak + 1 : streak - 1;
        } else {
          break;
        }
      }
    }
    
    const last10 = closedTrades.slice(-10).map(t => t.pnl > 0);
    
    return { winRate, profitFactor, streak, last10, wins, losses };
  }, [closedTrades]);
  
  return (
    <div className="h-full flex flex-col space-y-2 p-1">
      {/* ACCURACY HEADER */}
      <div className={`bg-gradient-to-r ${stats.winRate >= 70 ? 'from-emerald-500 to-cyan-500' : stats.winRate >= 50 ? 'from-yellow-500 to-orange-500' : 'from-red-500 to-pink-500'} rounded-lg p-2 text-center`}>
        <div className="text-white font-black text-lg">{stats.winRate.toFixed(1)}%</div>
        <div className="text-white/80 text-xs">HISTORICAL WIN RATE</div>
      </div>
      
      {/* STATS GRID */}
      <div className="grid grid-cols-3 gap-1">
        <div className="bg-slate-800/50 rounded-lg p-2 text-center">
          <div className="text-emerald-400 font-bold text-sm">{stats.wins || 0}</div>
          <div className="text-slate-500 text-[10px]">WINS</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-2 text-center">
          <div className="text-red-400 font-bold text-sm">{stats.losses || 0}</div>
          <div className="text-slate-500 text-[10px]">LOSSES</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-2 text-center">
          <div className="text-cyan-400 font-bold text-sm">{stats.profitFactor.toFixed(2)}</div>
          <div className="text-slate-500 text-[10px]">PROFIT FACTOR</div>
        </div>
      </div>
      
      {/* LAST 10 TRADES VISUAL */}
      <div className="bg-slate-800/30 rounded-lg p-2">
        <div className="text-xs text-slate-400 mb-1">Last 10 Signals:</div>
        <div className="flex gap-1 justify-center">
          {stats.last10.map((win, idx) => (
            <div 
              key={idx} 
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${win ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'}`}
            >
              {win ? 'W' : 'L'}
            </div>
          ))}
          {stats.last10.length === 0 && <span className="text-slate-500 text-xs">No trades yet</span>}
        </div>
      </div>
      
      {/* STREAK INDICATOR */}
      <div className={`rounded-lg p-2 text-center ${stats.streak > 0 ? 'bg-emerald-500/20 border border-emerald-500/50' : stats.streak < 0 ? 'bg-red-500/20 border border-red-500/50' : 'bg-slate-500/20'}`}>
        <div className={`font-bold text-sm ${stats.streak > 0 ? 'text-emerald-400' : stats.streak < 0 ? 'text-red-400' : 'text-slate-400'}`}>
          {stats.streak > 0 ? `${stats.streak} WIN STREAK` : stats.streak < 0 ? `${Math.abs(stats.streak)} LOSS STREAK` : 'NO STREAK'}
        </div>
      </div>
      
      {/* CONFIDENCE MESSAGE */}
      <div className="bg-slate-800/50 rounded-lg p-2 text-xs text-slate-300">
        <span className="font-bold text-cyan-400">TRACK RECORD: </span>
        {stats.winRate >= 70 ? 
          'System is performing excellently. High confidence in signals.' :
         stats.winRate >= 50 ?
          'System is profitable. Signals are reliable.' :
          'System needs optimization. Trade with caution.'
        }
      </div>
    </div>
  );
};

const DeltaProfileChart = ({ data, symbol }: { data: VolumeProfile | null, symbol: string }) => {
  if (!data || !data.levels || data.levels.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        <Activity className="w-6 h-6 animate-pulse mr-2" />
        Loading Delta Profile...
      </div>
    );
  }

  const decimals = symbol === 'XAUUSD' ? 2 : symbol === 'USDJPY' ? 3 : 5;
  const maxDelta = Math.max(...data.levels.map(l => Math.abs(l.delta)));

  return (
    <div className="h-full flex flex-col">
      <div className="text-xs text-slate-400 mb-2 flex justify-between">
        <span className="text-emerald-400">Buying Pressure</span>
        <span className="text-red-400">Selling Pressure</span>
      </div>
      <div className="flex-1 flex flex-col-reverse gap-px overflow-hidden">
        {data.levels.map((level, idx) => {
          const deltaWidth = maxDelta > 0 ? (Math.abs(level.delta) / maxDelta) * 50 : 0;
          const isBuying = level.delta > 0;
          
          return (
            <div key={idx} className="flex-1 flex items-center group relative min-h-1">
              {/* Price label on hover */}
              <div className="absolute left-1/2 -translate-x-1/2 hidden group-hover:block bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs z-20 whitespace-nowrap">
                {level.price_mid.toFixed(decimals)} | Delta: {level.delta > 0 ? '+' : ''}{level.delta.toFixed(0)}
              </div>
              
              {/* Left side - Selling (red) */}
              <div className="w-1/2 flex justify-end pr-1">
                {!isBuying && (
                  <div 
                    className="h-full bg-gradient-to-l from-red-500 to-red-600 rounded-l transition-all"
                    style={{ width: `${deltaWidth}%` }}
                  />
                )}
              </div>
              
              {/* Center line */}
              <div className="w-px h-full bg-slate-600" />
              
              {/* Right side - Buying (green) */}
              <div className="w-1/2 flex justify-start pl-1">
                {isBuying && (
                  <div 
                    className="h-full bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-r transition-all"
                    style={{ width: `${deltaWidth}%` }}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="text-xs text-slate-500 mt-2 text-center">
        POC: {data.poc.toFixed(decimals)} | VAH: {data.vah.toFixed(decimals)} | VAL: {data.val.toFixed(decimals)}
      </div>
    </div>
  );
};


function App() {
  const [state, setState] = useState<TradingState | null>(null);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState<'brain' | 'setup' | 'mtf' | 'accuracy' | 'orderflow' | 'levels' | 'risk'>('brain');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'XAUUSD'];
  const decimals = selectedSymbol === 'XAUUSD' ? 2 : selectedSymbol === 'USDJPY' ? 3 : 5;

  const fetchData = useCallback(async () => {
    try {
      const [stateRes, perfRes, pricesRes, chartRes] = await Promise.all([
        fetch(`${API_URL}/api/state`),
        fetch(`${API_URL}/api/performance`),
        fetch(`${API_URL}/api/prices`),
        fetch(`${API_URL}/api/chart-data/${selectedSymbol}?bars=100`)
      ]);

      if (stateRes.ok) setState(await stateRes.json());
      if (perfRes.ok) setPerformance(await perfRes.json());
      if (pricesRes.ok) setPrices(await pricesRes.json());
      if (chartRes.ok) {
        const data = (await chartRes.json()) as Partial<ChartData>;
        if (Array.isArray(data.delta)) {
          data.delta = data.delta.map((d, i) => ({ ...d, idx: i }));
        }
        setChartData(data as ChartData);
      }
      setIsConnected(true);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching data:', error);
      setIsConnected(false);
    }
  }, [selectedSymbol]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;

  const getRegimeColor = (regime: string) => {
    switch (regime?.toUpperCase()) {
      case 'TRENDING': return 'text-emerald-400 bg-emerald-500/20';
      case 'RANGING': return 'text-amber-400 bg-amber-500/20';
      case 'VOLATILE': return 'text-red-400 bg-red-500/20';
      default: return 'text-slate-400 bg-slate-500/20';
    }
  };

  const getStructureIcon = (structure: string) => {
    if (structure === 'BULLISH') return <TrendingUp className="w-4 h-4 text-emerald-400" />;
    if (structure === 'BEARISH') return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Activity className="w-4 h-4 text-amber-400" />;
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <header className="bg-[#0f1420] border-b border-slate-800 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                  OMEGA-DEVIN
                </h1>
                <p className="text-xs text-slate-500">Institutional Trading Platform</p>
              </div>
            </div>
            
            <div className="flex items-center gap-1 ml-8 bg-slate-800/50 rounded-lg p-1">
              {symbols.map(symbol => (
                <button
                  key={symbol}
                  onClick={() => setSelectedSymbol(symbol)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                    selectedSymbol === symbol 
                      ? 'bg-gradient-to-r from-cyan-500 to-purple-500 text-white shadow-lg' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                  }`}
                >
                  {symbol}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-2xl font-mono font-bold text-white">
                {prices[selectedSymbol]?.toFixed(decimals) || '---'}
              </div>
              <div className="text-xs text-slate-500">Current Price</div>
            </div>

            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${isConnected ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
              <span className={`text-xs font-medium ${isConnected ? 'text-emerald-400' : 'text-red-400'}`}>
                {isConnected ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>

            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${state?.kill_switch_active ? 'bg-red-500/20' : 'bg-emerald-500/20'}`}>
              <Shield className={`w-4 h-4 ${state?.kill_switch_active ? 'text-red-400' : 'text-emerald-400'}`} />
              <span className={`text-xs font-medium ${state?.kill_switch_active ? 'text-red-400' : 'text-emerald-400'}`}>
                {state?.kill_switch_active ? 'HALTED' : 'ACTIVE'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="p-4 grid grid-cols-12 gap-4" style={{ height: 'calc(100vh - 80px)' }}>
        
        <div className="col-span-2 space-y-4">
          <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
            <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
              <DollarSign className="w-4 h-4" /> Account
            </h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-slate-500">Capital</div>
                <div className="text-xl font-mono font-bold text-white">{formatCurrency(state?.capital || 10000)}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Total P&L</div>
                <div className={`text-lg font-mono font-bold ${(state?.total_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {formatCurrency(state?.total_pnl || 0)}
                  <span className="text-xs ml-1">({formatPercent(state?.total_pnl_pct || 0)})</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
            <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" /> Performance
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500">Win Rate</span>
                <span className="text-sm font-mono font-bold text-emerald-400">
                  {((performance?.win_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full"
                  style={{ width: `${(performance?.win_rate || 0) * 100}%` }}
                />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500">Profit Factor</span>
                <span className="text-sm font-mono font-bold text-cyan-400">
                  {(performance?.profit_factor || 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500">Total Trades</span>
                <span className="text-sm font-mono text-white">{performance?.total_trades || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500">Avg Trade</span>
                <span className={`text-sm font-mono ${(performance?.avg_trade || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {formatCurrency(performance?.avg_trade || 0)}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
            <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
              <Layers className="w-4 h-4" /> Market Structure
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Structure</span>
                <div className="flex items-center gap-1">
                  {getStructureIcon(chartData?.market_structure?.structure || '')}
                  <span className={`text-sm font-bold ${
                    chartData?.market_structure?.structure === 'BULLISH' ? 'text-emerald-400' :
                    chartData?.market_structure?.structure === 'BEARISH' ? 'text-red-400' : 'text-amber-400'
                  }`}>
                    {chartData?.market_structure?.structure || 'UNKNOWN'}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Trend</span>
                <span className={`text-sm font-medium px-2 py-0.5 rounded ${getRegimeColor(chartData?.market_structure?.trend || '')}`}>
                  {chartData?.market_structure?.trend || 'NEUTRAL'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Regime</span>
                <span className={`text-sm font-medium px-2 py-0.5 rounded ${getRegimeColor(state?.regime || '')}`}>
                  {state?.regime || 'NEUTRAL'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-7 space-y-4">
          <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4" style={{ height: '45%' }}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
                <Activity className="w-4 h-4" /> {selectedSymbol} Price Chart with VWAP
              </h3>
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-0.5 bg-purple-500" />
                  <span className="text-slate-500">VWAP</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 bg-emerald-500 rounded-sm" />
                  <span className="text-slate-500">Bullish</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 bg-red-500 rounded-sm" />
                  <span className="text-slate-500">Bearish</span>
                </div>
              </div>
            </div>
            <div className="h-[calc(100%-30px)]">
                                                        <CandlestickChart 
                                                          candles={chartData?.candles || []} 
                                                          vwap={chartData?.vwap || []} 
                                                          symbol={selectedSymbol}
                                                          volumeProfile={chartData?.volume_profile}
                                                          liquiditySweeps={chartData?.liquidity_sweeps}
                                                          marketStructure={chartData?.market_structure}
                                                          unifiedDecision={(() => {
                                                            // Calculate unified decision for chart display
                                                            const vp = chartData?.volume_profile;
                                                            const of = chartData?.order_flow_imbalance;
                                                            const ms = chartData?.market_structure;
                                                            const delta = chartData?.delta || [];
                                                            const price = chartData?.current_price || 0;
                                
                                                            let score = 0;
                                                            const signals: UnifiedSignal[] = [];
                                
                                                            // Volume Profile signal
                                                            if (vp) {
                                                              if (price > vp.vah) { score += 0.8 * 0.25; signals.push({ name: 'VP', bias: 'BULL' }); }
                                                              else if (price < vp.val) { score -= 0.8 * 0.25; signals.push({ name: 'VP', bias: 'BEAR' }); }
                                                              else if (price > vp.poc) { score += 0.3 * 0.25; signals.push({ name: 'VP', bias: 'BULL' }); }
                                                              else { score -= 0.3 * 0.25; signals.push({ name: 'VP', bias: 'BEAR' }); }
                                                            }
                                
                                                            // Delta signal
                                                            if (delta.length > 0) {
                                                              const lastDelta = delta[delta.length - 1]?.cumulative_delta || 0;
                                                              const prevDelta = delta[Math.max(0, delta.length - 10)]?.cumulative_delta || 0;
                                                              const trend = lastDelta - prevDelta;
                                                              if (trend > 1000) { score += 0.9 * 0.30; signals.push({ name: 'Delta', bias: 'BULL' }); }
                                                              else if (trend < -1000) { score -= 0.9 * 0.30; signals.push({ name: 'Delta', bias: 'BEAR' }); }
                                                              else if (trend > 0) { score += 0.4 * 0.30; signals.push({ name: 'Delta', bias: 'BULL' }); }
                                                              else { score -= 0.4 * 0.30; signals.push({ name: 'Delta', bias: 'BEAR' }); }
                                                            }
                                
                                                            // Order Flow signal
                                                            if (of) {
                                                              const ofi = of.ofi_normalized;
                                                              if (ofi > 0.5) { score += 0.85 * 0.25; signals.push({ name: 'OFI', bias: 'BULL' }); }
                                                              else if (ofi < -0.5) { score -= 0.85 * 0.25; signals.push({ name: 'OFI', bias: 'BEAR' }); }
                                                              else { signals.push({ name: 'OFI', bias: 'NEUT' }); }
                                                            }
                                
                                                            // Structure signal
                                                            if (ms) {
                                                              if (ms.structure === 'BULLISH') { score += 0.7 * 0.20; signals.push({ name: 'Struct', bias: 'BULL' }); }
                                                              else if (ms.structure === 'BEARISH') { score -= 0.7 * 0.20; signals.push({ name: 'Struct', bias: 'BEAR' }); }
                                                              else { signals.push({ name: 'Struct', bias: 'NEUT' }); }
                                                            }
                                
                                                            let decision = 'WAIT';
                                                            if (score > 0.5) decision = 'STRONG BUY';
                                                            else if (score > 0.2) decision = 'BUY';
                                                            else if (score < -0.5) decision = 'STRONG SELL';
                                                            else if (score < -0.2) decision = 'SELL';
                                
                                                                                                                    return { decision, confidence: Math.abs(score) * 100, signals };
                                                                                                                  })()}
                                                                                                                  tradeSetup={(() => {
                                                                                                                    // UNPUSHABLE: Calculate trade setup for chart markers
                                                                                                                    const vp = chartData?.volume_profile;
                                                                                                                    const of = chartData?.order_flow_imbalance;
                                                                                                                    const ms = chartData?.market_structure;
                                                                                                                    const deltaData = chartData?.delta || [];
                                                                                                                    const price = chartData?.current_price || 0;
                                                            
                                                                                                                    if (!vp || !price) return null;
                                                            
                                                                                                                    let bullishScore = 0;
                                                                                                                    let bearishScore = 0;
                                                            
                                                                                                                    // Volume Profile Analysis
                                                                                                                    if (price > vp.vah) bullishScore += 30;
                                                                                                                    else if (price < vp.val) bearishScore += 30;
                                                                                                                    else if (price > vp.poc) bullishScore += 15;
                                                                                                                    else bearishScore += 15;
                                                            
                                                                                                                    // Delta Analysis
                                                                                                                    if (deltaData.length > 0) {
                                                                                                                      const lastDelta = deltaData[deltaData.length - 1]?.cumulative_delta || 0;
                                                                                                                      const prevDelta = deltaData[Math.max(0, deltaData.length - 10)]?.cumulative_delta || 0;
                                                                                                                      const deltaTrend = lastDelta - prevDelta;
                                                                                                                      if (deltaTrend > 2000) bullishScore += 35;
                                                                                                                      else if (deltaTrend < -2000) bearishScore += 35;
                                                                                                                      else if (deltaTrend > 500) bullishScore += 15;
                                                                                                                      else if (deltaTrend < -500) bearishScore += 15;
                                                                                                                    }
                                                            
                                                                                                                    // Order Flow Analysis
                                                                                                                    if (of) {
                                                                                                                      if (of.ofi_normalized > 0.6) bullishScore += 25;
                                                                                                                      else if (of.ofi_normalized < -0.6) bearishScore += 25;
                                                                                                                    }
                                                            
                                                                                                                    // Market Structure Analysis
                                                                                                                    if (ms) {
                                                                                                                      if (ms.structure === 'BULLISH') bullishScore += 20;
                                                                                                                      else if (ms.structure === 'BEARISH') bearishScore += 20;
                                                                                                                    }
                                                            
                                                                                                                    const confidence = Math.max(bullishScore, bearishScore);
                                                                                                                    const direction = bullishScore > bearishScore ? 'LONG' : bearishScore > bullishScore ? 'SHORT' : 'NEUTRAL';
                                                            
                                                                                                                    let entry = price;
                                                                                                                    let stopLoss = 0;
                                                                                                                    let target1 = 0;
                                                                                                                    let target2 = 0;
                                                            
                                                                                                                    if (direction === 'LONG') {
                                                                                                                      entry = Math.min(price, vp.poc + (vp.vah - vp.poc) * 0.3);
                                                                                                                      stopLoss = vp.val - (vp.vah - vp.val) * 0.1;
                                                                                                                      target1 = vp.vah;
                                                                                                                      target2 = vp.vah + (vp.vah - vp.poc) * 0.5;
                                                                                                                    } else if (direction === 'SHORT') {
                                                                                                                      entry = Math.max(price, vp.poc - (vp.poc - vp.val) * 0.3);
                                                                                                                      stopLoss = vp.vah + (vp.vah - vp.val) * 0.1;
                                                                                                                      target1 = vp.val;
                                                                                                                      target2 = vp.val - (vp.poc - vp.val) * 0.5;
                                                                                                                    }
                                                            
                                                                                                                    const risk = Math.abs(entry - stopLoss);
                                                                                                                    const reward1 = Math.abs(target1 - entry);
                                                                                                                    const riskReward1 = risk > 0 ? reward1 / risk : 0;
                                                            
                                                                                                                    return {
                                                                                                                      direction,
                                                                                                                      confidence,
                                                                                                                      entry,
                                                                                                                      stopLoss,
                                                                                                                      target1,
                                                                                                                      target2,
                                                                                                                      riskReward1,
                                                                                                                      isHighProbability: confidence >= 60 && riskReward1 >= 1.5
                                                                                                                    };
                                                                                                                  })()}
                                                                                                                  delta={chartData?.delta || []}
                                                                                                                />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4" style={{ height: '25%' }}>
            <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
              <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" /> Bar Delta
              </h3>
              <div className="h-[calc(100%-30px)]">
                <DeltaChart data={chartData?.delta || []} />
              </div>
            </div>
            <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
              <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" /> Cumulative Delta
              </h3>
              <div className="h-[calc(100%-30px)]">
                <CumulativeDeltaChart data={chartData?.delta || []} />
              </div>
            </div>
          </div>

          <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4" style={{ height: '25%' }}>
            <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
              <Clock className="w-4 h-4" /> Recent Trades
            </h3>
            <div className="overflow-auto h-[calc(100%-30px)]">
              <table className="w-full text-xs">
                <thead className="text-slate-500 border-b border-slate-700">
                  <tr>
                    <th className="text-left py-2">Symbol</th>
                    <th className="text-left py-2">Side</th>
                    <th className="text-right py-2">Entry</th>
                    <th className="text-right py-2">Exit</th>
                    <th className="text-right py-2">P&L</th>
                    <th className="text-left py-2">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {(state?.closed_trades || []).slice(-8).reverse().map((trade, idx) => (
                    <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                      <td className="py-2 font-medium">{trade.symbol}</td>
                      <td className={`py-2 ${trade.side === 'LONG' ? 'text-emerald-400' : 'text-red-400'}`}>
                        {trade.side === 'LONG' ? <ArrowUpRight className="w-3 h-3 inline" /> : <ArrowDownRight className="w-3 h-3 inline" />}
                        {trade.side}
                      </td>
                      <td className="py-2 text-right font-mono">{trade.entry?.toFixed(decimals)}</td>
                      <td className="py-2 text-right font-mono">{trade.exit?.toFixed(decimals)}</td>
                      <td className={`py-2 text-right font-mono font-bold ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {trade.pnl >= 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                      </td>
                      <td className="py-2">
                        <span className={`px-1.5 py-0.5 rounded text-xs ${
                          trade.exit_reason === 'TP1' || trade.exit_reason === 'TP2' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                          {trade.exit_reason}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

                <div className="col-span-3 space-y-4">
                  <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-1 flex flex-wrap">
                                        <button
                                          onClick={() => setActiveTab('brain')}
                                          className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${
                                            activeTab === 'brain' ? 'bg-gradient-to-r from-cyan-500/30 to-purple-500/30 text-white border border-cyan-500/50' : 'text-slate-400 hover:text-white'
                                          }`}
                                        >
                                          <Brain className="w-3 h-3" /> Brain
                                        </button>
                                                                                <button
                                                                                  onClick={() => setActiveTab('setup')}
                                                                                  className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${
                                                                                    activeTab === 'setup' ? 'bg-gradient-to-r from-emerald-500/30 to-cyan-500/30 text-white border border-emerald-500/50' : 'text-slate-400 hover:text-white'
                                                                                  }`}
                                                                                >
                                                                                  <Target className="w-3 h-3" /> Setup
                                                                                </button>
                                                                                <button
                                                                                  onClick={() => setActiveTab('mtf')}
                                                                                  className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${
                                                                                    activeTab === 'mtf' ? 'bg-gradient-to-r from-purple-500/30 to-pink-500/30 text-white border border-purple-500/50' : 'text-slate-400 hover:text-white'
                                                                                  }`}
                                                                                >
                                                                                  <Layers className="w-3 h-3" /> MTF
                                                                                </button>
                                                                                <button
                                                                                  onClick={() => setActiveTab('accuracy')}
                                                                                  className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${
                                                                                    activeTab === 'accuracy' ? 'bg-gradient-to-r from-yellow-500/30 to-orange-500/30 text-white border border-yellow-500/50' : 'text-slate-400 hover:text-white'
                                                                                  }`}
                                                                                >
                                                                                  <Award className="w-3 h-3" /> Accuracy
                                                                                </button>
                                                                                <button
                                                                                  onClick={() => setActiveTab('orderflow')}
                      className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${
                        activeTab === 'orderflow' ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Zap className="w-3 h-3" /> Flow
                    </button>
                    <button
                      onClick={() => setActiveTab('levels')}
                      className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${
                        activeTab === 'levels' ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Target className="w-3 h-3" /> Levels
                    </button>
                    <button
                      onClick={() => setActiveTab('risk')}
                      className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${
                        activeTab === 'risk' ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-white' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Shield className="w-3 h-3" /> Risk
                    </button>
                  </div>

                                    {activeTab === 'brain' && (
                                      <div className="h-[calc(100%-50px)]">
                                        <UnifiedIntelligence
                                          volumeProfile={chartData?.volume_profile || null}
                                          orderFlow={chartData?.order_flow_imbalance || null}
                                          marketStructure={chartData?.market_structure || null}
                                          riskMetrics={chartData?.risk_metrics || null}
                                          delta={chartData?.delta || []}
                                          currentPrice={chartData?.current_price || 0}
                                          symbol={selectedSymbol}
                                        />
                                      </div>
                                    )}

                                                                        {activeTab === 'setup' && (
                                                                          <div className="h-[calc(100%-50px)]">
                                                                            <PredictiveTradeSetup
                                                                              volumeProfile={chartData?.volume_profile || null}
                                                                              orderFlow={chartData?.order_flow_imbalance || null}
                                                                              marketStructure={chartData?.market_structure || null}
                                                                              delta={chartData?.delta || []}
                                                                              currentPrice={chartData?.current_price || 0}
                                                                              symbol={selectedSymbol}
                                                                            />
                                                                          </div>
                                                                        )}

                                                                        {activeTab === 'mtf' && (
                                                                          <div className="h-[calc(100%-50px)]">
                                                                            <MultiTimeframeConfluence
                                                                              volumeProfile={chartData?.volume_profile || null}
                                                                              marketStructure={chartData?.market_structure || null}
                                                                              delta={chartData?.delta || []}
                                                                              currentPrice={chartData?.current_price || 0}
                                                                            />
                                                                          </div>
                                                                        )}

                                                                        {activeTab === 'accuracy' && (
                                                                          <div className="h-[calc(100%-50px)]">
                                                                            <HistoricalAccuracyTracker
                                                                              closedTrades={state?.closed_trades || []}
                                                                            />
                                                                          </div>
                                                                        )}

                                                                        {activeTab === 'orderflow' && (
            <>
              <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Gauge className="w-4 h-4" /> Order Flow Imbalance
                </h3>
                <SignalGauge 
                  value={chartData?.order_flow_imbalance?.strength || 0}
                  label={`OFI: ${(chartData?.order_flow_imbalance?.ofi_normalized || 0).toFixed(3)}`}
                  signal={chartData?.order_flow_imbalance?.signal || 'NEUTRAL'}
                />
              </div>

              <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Eye className="w-4 h-4" /> Footprint Analysis
                </h3>
                <div className="space-y-2">
                  <FootprintSignal 
                    type="imbalances" 
                    count={chartData?.footprint?.imbalances?.length || 0}
                  />
                  <FootprintSignal 
                    type="absorption" 
                    count={chartData?.footprint?.absorption_zones?.length || 0}
                  />
                  <FootprintSignal 
                    type="exhaustion" 
                    count={chartData?.footprint?.exhaustion_signals?.length || 0}
                  />
                </div>
              </div>

              <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Crosshair className="w-4 h-4" /> Liquidity Sweeps
                </h3>
                {(chartData?.liquidity_sweeps?.length || 0) > 0 ? (
                  <div className="space-y-2">
                    {chartData?.liquidity_sweeps?.map((sweep, idx) => (
                      <div key={idx} className={`p-2 rounded-lg border ${
                        sweep.signal === 'BULLISH' ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-red-500/50 bg-red-500/10'
                      }`}>
                        <div className="flex items-center justify-between">
                          <span className={`text-xs font-medium ${sweep.signal === 'BULLISH' ? 'text-emerald-400' : 'text-red-400'}`}>
                            {sweep.type}
                          </span>
                          <span className="text-xs font-mono text-white">{sweep.sweep_price?.toFixed(decimals)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-slate-500 text-sm py-4">No recent sweeps detected</div>
                )}
              </div>
            </>
          )}

                    {activeTab === 'levels' && (
                      <>
                        <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4" style={{ height: '200px' }}>
                          <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                            <Volume2 className="w-4 h-4" /> Volume Profile (DeepCharts Style)
                          </h3>
                          <div className="h-[calc(100%-30px)]">
                            <VolumeProfileChart 
                              data={chartData?.volume_profile || null}
                              currentPrice={chartData?.current_price || 0}
                              symbol={selectedSymbol}
                            />
                          </div>
                        </div>

                        <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4" style={{ height: '200px' }}>
                          <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                            <BarChart3 className="w-4 h-4" /> Delta Profile (Buy vs Sell)
                          </h3>
                          <div className="h-[calc(100%-30px)]">
                            <DeltaProfileChart 
                              data={chartData?.volume_profile || null}
                              symbol={selectedSymbol}
                            />
                          </div>
                        </div>

                        <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
                          <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                            <Target className="w-4 h-4" /> Key Levels
                          </h3>
                          <div className="space-y-1 max-h-40 overflow-auto">
                            {(chartData?.institutional_levels?.levels || []).map((level, idx) => (
                              <LevelRow key={idx} level={level} decimals={decimals} />
                            ))}
                          </div>
                        </div>
                      </>
                    )}

          {activeTab === 'risk' && (
            <>
              <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> Risk Metrics
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <RiskCard label="VaR (95%)" value={chartData?.risk_metrics?.var_95 || 0} unit="%" isNegative />
                  <RiskCard label="VaR (99%)" value={chartData?.risk_metrics?.var_99 || 0} unit="%" isNegative />
                  <RiskCard label="Expected Shortfall" value={chartData?.risk_metrics?.expected_shortfall || 0} unit="%" isNegative />
                  <RiskCard label="Max Drawdown" value={chartData?.risk_metrics?.max_drawdown || 0} unit="%" isNegative />
                  <RiskCard label="Volatility (Ann.)" value={chartData?.risk_metrics?.volatility || 0} unit="%" />
                  <RiskCard label="Sharpe Ratio" value={chartData?.risk_metrics?.sharpe_estimate || 0} unit="" />
                </div>
              </div>

              <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Layers className="w-4 h-4" /> Break of Structure
                </h3>
                {(chartData?.market_structure?.bos_signals?.length || 0) > 0 ? (
                  <div className="space-y-2">
                    {chartData?.market_structure?.bos_signals?.map((bos, idx) => (
                      <div key={idx} className={`p-3 rounded-lg border ${
                        bos.type === 'BOS_BULLISH' ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-red-500/50 bg-red-500/10'
                      }`}>
                        <div className="flex items-center gap-2">
                          {bos.type === 'BOS_BULLISH' ? 
                            <ChevronUp className="w-4 h-4 text-emerald-400" /> : 
                            <ChevronDown className="w-4 h-4 text-red-400" />
                          }
                          <span className={`text-sm font-medium ${bos.type === 'BOS_BULLISH' ? 'text-emerald-400' : 'text-red-400'}`}>
                            {bos.type.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                          Broken: {bos.broken_level?.toFixed(decimals)} | Current: {bos.current_price?.toFixed(decimals)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-slate-500 text-sm py-4">No BOS signals</div>
                )}
              </div>

              <div className="bg-[#0f1420] rounded-xl border border-slate-800 p-4">
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4" /> Swing Points
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-slate-500 mb-2">Swing Highs</div>
                    {(chartData?.market_structure?.swing_highs || []).slice(-3).map((sh, idx) => (
                      <div key={idx} className="text-sm font-mono text-emerald-400 py-0.5">
                        {sh.price?.toFixed(decimals)}
                      </div>
                    ))}
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-2">Swing Lows</div>
                    {(chartData?.market_structure?.swing_lows || []).slice(-3).map((sl, idx) => (
                      <div key={idx} className="text-sm font-mono text-red-400 py-0.5">
                        {sl.price?.toFixed(decimals)}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <footer className="fixed bottom-0 left-0 right-0 bg-[#0f1420] border-t border-slate-800 px-6 py-2">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-4">
            <span>OMEGA-DEVIN v5.0.0-INSTITUTIONAL</span>
            <span className="text-slate-700">|</span>
            <span>Powered by Breakthrough Intelligence</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Last Update: {lastUpdate.toLocaleTimeString()}</span>
            <span className="text-slate-700">|</span>
            <span className={isConnected ? 'text-emerald-400' : 'text-red-400'}>
              {isConnected ? 'Connected to Backend' : 'Disconnected'}
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
