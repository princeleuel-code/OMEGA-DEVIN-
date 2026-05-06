import { useMemo, useState, type MouseEvent, type ReactNode } from 'react';

type TerminalMode = 'capsule' | 'command';
type ComprehensionMode = 'beginner' | 'expert';
type AutonomyMode = 'manual' | 'paper';
type VerdictLabel = 'EXECUTE' | 'WAIT' | 'EXPLICIT_ABSTAIN' | 'HARD_LOCK';
type Direction = 'LONG' | 'SHORT' | 'NEUTRAL';
type TrappedSide = 'BUYERS' | 'SELLERS' | 'NONE';
type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
type AgentBias = 'BULLISH' | 'BEARISH' | 'NEUTRAL';
type Tone = 'cyan' | 'green' | 'gold' | 'red' | 'neutral';

interface PriceLevel {
  price: number;
  bidVolume: number;
  askVolume: number;
  imbalance: number;
  absorption: number;
}

interface InternalProfileLevel {
  price: number;
  volume: number;
  side: 'buy' | 'sell' | 'neutral';
}

interface RejectionEdge {
  side: 'upper' | 'lower';
  strength: number;
  price: number;
}

interface AcceptanceCore {
  low: number;
  high: number;
  strength: number;
}

interface CandleTruthPacket {
  id: string;
  timestamp: string;
  symbol: string;
  timeframe: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  bidVolume: number;
  askVolume: number;
  delta: number;
  cumulativeDelta: number;
  internalProfile: InternalProfileLevel[];
  priceLevels: PriceLevel[];
  poc: number;
  vah: number;
  val: number;
  acceptanceCore: AcceptanceCore;
  deltaSpine: number[];
  absorptionNodes: PriceLevel[];
  imbalanceLadder: PriceLevel[];
  liquiditySweepHigh: boolean;
  liquiditySweepLow: boolean;
  fairValueGap: boolean;
  structuralVoid: boolean;
  trappedSide: TrappedSide;
  rejectionEdges: RejectionEdge[];
  toxicity: number;
  trustScore: number;
  continuationProbability: number;
  reversalProbability: number;
  manipulationRisk: number;
  beginnerExplanation: string;
  expertExplanation: string;
  verdict: VerdictLabel;
}

interface MarketState {
  symbol: string;
  timeframe: string;
  session: string;
  candles: CandleTruthPacket[];
  regime: string;
  higherTimeframeTrend: string;
  activePlaybook: string;
  eventRisk: RiskLevel;
  dataLatencyMs: number;
  replaySync: number;
  truthSync: number;
  systemHealth: number;
}

interface AgentAnalysis {
  agentName: string;
  confidence: number;
  evidence: string[];
  bias: AgentBias;
  recommendation: string;
  riskFlag: boolean;
  disagreementFlag: boolean;
  lastUpdated: string;
  canInfluenceExecution: boolean;
}

interface VerdictDecision {
  verdict: VerdictLabel;
  direction: Direction;
  confidence: number;
  reason: string;
  beginnerReason: string;
  expertReason: string;
  requiredConfirmation: string;
  invalidation: number;
  targets: number[];
  maxRisk: number;
  executionStyle: string;
  hardLockReasons: string[];
  expectedEdge: number;
  volatilityCost: number;
  spreadCost: number;
  slippageCost: number;
  marketImpact: number;
  liquidityRisk: number;
  driftDistrust: number;
  modelDisagreement: number;
  replaySimilarity: number;
  robustLowerBound: number;
  riskReward: number;
}

interface LedgerEvent {
  eventId: string;
  candleId: string;
  timestamp: string;
  dataChecksum: string;
  modelVersion: string;
  ruleVersion: string;
  evidenceUsed: string[];
  agentVotes: string[];
  confidenceBeforeDecision: number;
  verdict: VerdictLabel;
  outcomeAfterNCandles: string;
  promotedStatus: 'promoted' | 'held' | 'rejected';
  replayHash: string;
  humanOverride: string;
  riskGovernorStatus: string;
}

interface ManipulationAssessment {
  level: RiskLevel;
  score: number;
  evidence: string[];
  recommendedAction: 'trade allowed' | 'reduce size' | 'wait' | 'hard abstain';
}

interface RiskState {
  dailyMaxLossHit: boolean;
  spreadTooWide: boolean;
  liquidityInsufficient: boolean;
  eventRiskHigh: boolean;
  staleData: boolean;
  modelDisagreementHigh: boolean;
  manipulationRiskHigh: boolean;
  robustLowerBoundNegative: boolean;
  replaySimilarityWeak: boolean;
  hardLockActive: boolean;
  locks: string[];
}

interface Scenario {
  name: string;
  probability: number;
  path: string;
  cancellation: string;
}

interface BrittlePoint {
  name: string;
  whyItBreaks: string;
  technicalFix: string;
}

const clamp = (value: number, min = 0, max = 1) => Math.max(min, Math.min(max, value));
const fmt = (value: number, digits = 2) => value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
const pct = (value: number) => `${Math.round(value * 100)}%`;

const hashText = (input: string): string => {
  let hash = 0;
  for (let index = 0; index < input.length; index += 1) {
    hash = (hash * 31 + input.charCodeAt(index)) >>> 0;
  }
  return hash.toString(16).padStart(8, '0').slice(0, 8).toUpperCase();
};

const classForVerdict = (verdict: VerdictLabel) => {
  if (verdict === 'EXECUTE') return 'state-positive';
  if (verdict === 'WAIT') return 'state-wait';
  if (verdict === 'EXPLICIT_ABSTAIN') return 'state-danger';
  return 'state-lock';
};

const classForRisk = (level: RiskLevel) => {
  if (level === 'LOW') return 'state-positive';
  if (level === 'MEDIUM') return 'state-wait';
  return 'state-danger';
};

const createProfile = (low: number, high: number, open: number, close: number, pressure: number, volatility: number) => {
  const levels: InternalProfileLevel[] = [];
  const priceLevels: PriceLevel[] = [];
  const count = 12;
  const range = Math.max(high - low, 0.01);
  for (let index = 0; index < count; index += 1) {
    const price = low + (range * index) / (count - 1);
    const distanceFromClose = Math.abs(price - close) / range;
    const distanceFromOpen = Math.abs(price - open) / range;
    const centerWeight = 1 - Math.abs(index - (count - 1) / 2) / ((count - 1) / 2);
    const attackSkew = pressure * (index / (count - 1) - 0.5);
    const volume = Math.round(420 + 1400 * centerWeight + 240 * Math.sin(index * 1.7 + volatility));
    const askVolume = Math.round(volume * clamp(0.52 + attackSkew - distanceFromOpen * 0.08, 0.18, 0.82));
    const bidVolume = Math.max(0, volume - askVolume);
    const imbalance = Math.abs(askVolume - bidVolume) / Math.max(volume, 1);
    const absorption = clamp((distanceFromClose < 0.18 ? 0.65 : 0.2) + volatility * 0.08 + imbalance * 0.35, 0, 1);
    const side = askVolume > bidVolume * 1.18 ? 'buy' : bidVolume > askVolume * 1.18 ? 'sell' : 'neutral';
    levels.push({ price, volume, side });
    priceLevels.push({ price, bidVolume, askVolume, imbalance, absorption });
  }
  return { profile: levels, priceLevels };
};

const explainCandle = (
  sweepHigh: boolean,
  sweepLow: boolean,
  trappedSide: TrappedSide,
  trustScore: number,
  toxicity: number,
  delta: number,
) => {
  if (toxicity > 0.72) return 'The book is toxic. The move is not safe enough to trust.';
  if (sweepHigh && trappedSide === 'BUYERS') return 'Price swept above the old high, then rejected. Late buyers may be trapped.';
  if (sweepLow && trappedSide === 'SELLERS') return 'Sellers pushed down, but buyers defended the low and absorbed the attack.';
  if (trustScore > 0.72 && delta > 0) return 'Buyers are in control. The pullback held value and continuation is being watched.';
  if (trustScore > 0.72 && delta < 0) return 'Sellers are in control. Buyers failed to reclaim value.';
  return 'The market is mixed. Waiting is the edge until evidence improves.';
};

function DataAdapterMock(): MarketState {
  const symbol = 'NQ-MICRO';
  const timeframe = '5m';
  const candles: CandleTruthPacket[] = [];
  let price = 5274;
  let cumulativeDelta = 0;
  for (let index = 0; index < 34; index += 1) {
    const wave = Math.sin(index * 0.58) * 8 + Math.cos(index * 0.19) * 4;
    const shock = index === 11 ? -16 : index === 19 ? 22 : index === 27 ? -11 : 0;
    const open = price;
    const body = Math.sin(index * 0.74) * 5 + Math.cos(index * 0.31) * 3 + shock * 0.35;
    const close = open + body;
    const high = Math.max(open, close) + 4.5 + Math.abs(Math.sin(index * 0.47)) * 8 + (index === 19 ? 15 : 0);
    const low = Math.min(open, close) - 4.5 - Math.abs(Math.cos(index * 0.53)) * 7 - (index === 11 ? 13 : 0);
    const pressure = clamp((close - open) / Math.max(high - low, 0.1), -1, 1);
    const volatility = Math.abs(high - low) / 28;
    const { profile, priceLevels } = createProfile(low, high, open, close, pressure, volatility);
    const volume = Math.round(9200 + Math.abs(body) * 560 + volatility * 2800 + (index === 19 || index === 11 ? 5400 : 0));
    const askVolume = Math.round(volume * clamp(0.5 + pressure * 0.42 + Math.sin(index * 0.41) * 0.08, 0.22, 0.78));
    const bidVolume = volume - askVolume;
    const delta = askVolume - bidVolume;
    cumulativeDelta += delta;
    const sortedByVolume = [...profile].sort((a, b) => b.volume - a.volume);
    const poc = sortedByVolume[0].price;
    const vah = low + (high - low) * 0.68;
    const val = low + (high - low) * 0.32;
    const sweepHigh = index === 19 || (index > 2 && high > Math.max(...candles.slice(-5).map((candle) => candle.high)) && close < high - (high - low) * 0.42);
    const sweepLow = index === 11 || (index > 2 && low < Math.min(...candles.slice(-5).map((candle) => candle.low)) && close > low + (high - low) * 0.42);
    const trappedSide: TrappedSide = sweepHigh ? 'BUYERS' : sweepLow ? 'SELLERS' : Math.abs(delta) < volume * 0.04 ? 'NONE' : delta > 0 && close < open ? 'BUYERS' : delta < 0 && close > open ? 'SELLERS' : 'NONE';
    const absorptionNodes = priceLevels.filter((level) => level.absorption > 0.68).slice(0, 4);
    const imbalanceLadder = priceLevels.filter((level) => level.imbalance > 0.32).slice(0, 5);
    const fairValueGap = index > 0 && (low > candles[index - 1].high || high < candles[index - 1].low);
    const structuralVoid = volatility > 0.88 && Math.abs(delta) > volume * 0.24;
    const manipulationRisk = clamp((sweepHigh || sweepLow ? 0.28 : 0.08) + (structuralVoid ? 0.22 : 0) + volatility * 0.18 + (Math.abs(delta) / volume) * 0.18);
    const toxicity = clamp(manipulationRisk + (trappedSide !== 'NONE' ? 0.12 : 0) + (fairValueGap ? 0.1 : 0));
    const trustScore = clamp(0.82 - toxicity * 0.42 + Math.min(absorptionNodes.length, 4) * 0.035 - (Math.abs(delta) < volume * 0.03 ? 0.12 : 0));
    const continuationProbability = clamp(0.46 + pressure * 0.3 + trustScore * 0.22 - toxicity * 0.16);
    const reversalProbability = clamp(0.46 - pressure * 0.26 + (trappedSide !== 'NONE' ? 0.24 : 0) - trustScore * 0.08);
    const verdict: VerdictLabel = toxicity > 0.78 ? 'HARD_LOCK' : trustScore < 0.48 ? 'EXPLICIT_ABSTAIN' : trustScore < 0.66 ? 'WAIT' : 'EXECUTE';
    const rejectionEdges: RejectionEdge[] = [
      { side: 'upper', strength: clamp((high - Math.max(open, close)) / Math.max(high - low, 0.01)), price: high },
      { side: 'lower', strength: clamp((Math.min(open, close) - low) / Math.max(high - low, 0.01)), price: low },
    ];
    const deltaSpine = priceLevels.map((level) => level.askVolume - level.bidVolume);
    const beginnerExplanation = explainCandle(sweepHigh, sweepLow, trappedSide, trustScore, toxicity, delta);
    const expertExplanation = `Delta ${delta.toLocaleString()} / CVD ${cumulativeDelta.toLocaleString()} with POC ${fmt(poc)}, VAH ${fmt(vah)}, VAL ${fmt(val)}; toxicity ${pct(toxicity)}, trust ${pct(trustScore)}.`;
    candles.push({
      id: `ctp-${String(index + 1).padStart(3, '0')}`,
      timestamp: `09:${String(30 + index * 5).padStart(2, '0')}`,
      symbol,
      timeframe,
      open,
      high,
      low,
      close,
      volume,
      bidVolume,
      askVolume,
      delta,
      cumulativeDelta,
      internalProfile: profile,
      priceLevels,
      poc,
      vah,
      val,
      acceptanceCore: { low: val, high: vah, strength: trustScore },
      deltaSpine,
      absorptionNodes,
      imbalanceLadder,
      liquiditySweepHigh: sweepHigh,
      liquiditySweepLow: sweepLow,
      fairValueGap,
      structuralVoid,
      trappedSide,
      rejectionEdges,
      toxicity,
      trustScore,
      continuationProbability,
      reversalProbability,
      manipulationRisk,
      beginnerExplanation,
      expertExplanation,
      verdict,
    });
    price = close + wave * 0.12;
  }
  return {
    symbol,
    timeframe,
    session: 'US RTH',
    candles,
    regime: 'Auction rotation with sweep-risk expansion',
    higherTimeframeTrend: 'Bullish above accepted value; fragile below lower core',
    activePlaybook: 'Sweep → Absorption → Accepted Continuation',
    eventRisk: 'MEDIUM',
    dataLatencyMs: 42,
    replaySync: 0.91,
    truthSync: 0.97,
    systemHealth: 0.94,
  };
}

const assessManipulation = (candle: CandleTruthPacket): ManipulationAssessment => {
  const evidence: string[] = [];
  if (candle.structuralVoid) evidence.push('Hollow-book move: displacement exceeded supporting profile density.');
  if (candle.liquiditySweepHigh || candle.liquiditySweepLow) evidence.push('Liquidity sweep detected near prior auction edge.');
  if (candle.manipulationRisk > 0.52) evidence.push('Price-volume curve deformation above normal replay band.');
  if (candle.toxicity > 0.62) evidence.push('Toxicity halo active: order-flow support is weak for the move.');
  if (evidence.length === 0) evidence.push('No defensive manipulation signature crossed the warning threshold.');
  const level: RiskLevel = candle.manipulationRisk > 0.68 ? 'HIGH' : candle.manipulationRisk > 0.42 ? 'MEDIUM' : 'LOW';
  const recommendedAction = level === 'HIGH' ? 'hard abstain' : level === 'MEDIUM' ? 'wait' : candle.toxicity > 0.45 ? 'reduce size' : 'trade allowed';
  return { level, score: candle.manipulationRisk, evidence, recommendedAction };
};

const evaluateRiskGovernor = (decision: VerdictDecision, marketState: MarketState): RiskState => {
  const locks: string[] = [];
  const state = {
    dailyMaxLossHit: false,
    spreadTooWide: decision.spreadCost > 0.22,
    liquidityInsufficient: decision.liquidityRisk > 0.64,
    eventRiskHigh: marketState.eventRisk === 'HIGH',
    staleData: marketState.dataLatencyMs > 350,
    modelDisagreementHigh: decision.modelDisagreement > 0.36,
    manipulationRiskHigh: decision.marketImpact > 0.72,
    robustLowerBoundNegative: decision.robustLowerBound < 0,
    replaySimilarityWeak: decision.replaySimilarity < 0.58,
    hardLockActive: false,
    locks,
  };
  if (state.spreadTooWide) locks.push('Spread cost violates scalping constraint.');
  if (state.liquidityInsufficient) locks.push('Available liquidity is insufficient for the proposed path.');
  if (state.eventRiskHigh) locks.push('Event risk is high.');
  if (state.staleData) locks.push('Data freshness check failed.');
  if (state.modelDisagreementHigh) locks.push('Agent council disagreement is too high.');
  if (state.manipulationRiskHigh) locks.push('Manipulation risk breached safe limits.');
  if (state.robustLowerBoundNegative) locks.push('Robust lower bound is negative.');
  if (state.replaySimilarityWeak) locks.push('Replay similarity is weak.');
  state.hardLockActive = decision.verdict === 'HARD_LOCK' || locks.length > 0;
  return state;
};

const buildAgents = (candle: CandleTruthPacket, marketState: MarketState): AgentAnalysis[] => {
  const now = 'live mock';
  const bias: AgentBias = candle.delta > 500 ? 'BULLISH' : candle.delta < -500 ? 'BEARISH' : 'NEUTRAL';
  return [
    {
      agentName: 'Regime Agent', confidence: 0.81, evidence: [marketState.regime, marketState.higherTimeframeTrend], bias,
      recommendation: 'Use acceptance core as the operating boundary.', riskFlag: false, disagreementFlag: false, lastUpdated: now, canInfluenceExecution: true,
    },
    {
      agentName: 'Liquidity Agent', confidence: candle.liquiditySweepHigh || candle.liquiditySweepLow ? 0.88 : 0.64,
      evidence: [candle.liquiditySweepHigh ? 'Buy-side sweep registered.' : candle.liquiditySweepLow ? 'Sell-side sweep registered.' : 'No fresh sweep.'],
      bias: candle.liquiditySweepLow ? 'BULLISH' : candle.liquiditySweepHigh ? 'BEARISH' : 'NEUTRAL', recommendation: candle.liquiditySweepHigh ? 'Do not chase the breakout.' : 'Track acceptance after sweep.',
      riskFlag: candle.toxicity > 0.62, disagreementFlag: candle.trappedSide !== 'NONE' && bias !== 'NEUTRAL', lastUpdated: now, canInfluenceExecution: true,
    },
    {
      agentName: 'Volume Agent', confidence: clamp(0.54 + candle.imbalanceLadder.length * 0.08), evidence: [`POC ${fmt(candle.poc)}`, `${candle.imbalanceLadder.length} imbalance bands`, `${candle.absorptionNodes.length} absorption nodes`],
      bias, recommendation: 'Require volume to remain accepted inside the core.', riskFlag: candle.structuralVoid, disagreementFlag: Math.abs(candle.delta) < candle.volume * 0.04, lastUpdated: now, canInfluenceExecution: true,
    },
    {
      agentName: 'Risk Governor', confidence: 0.93, evidence: [`Toxicity ${pct(candle.toxicity)}`, `Manipulation ${pct(candle.manipulationRisk)}`], bias: 'NEUTRAL',
      recommendation: candle.verdict === 'HARD_LOCK' ? 'Hard lock execution.' : 'Permit only if confirmation prints.', riskFlag: candle.verdict === 'HARD_LOCK' || candle.toxicity > 0.6, disagreementFlag: false, lastUpdated: now, canInfluenceExecution: true,
    },
    {
      agentName: 'Replay Agent', confidence: clamp(0.62 + candle.trustScore * 0.23 - candle.manipulationRisk * 0.14), evidence: ['Replay cluster: sweep-absorption-continuation', 'Outcome window: 8 candles'],
      bias, recommendation: 'Promote only after post-trade proof.', riskFlag: candle.trustScore < 0.55, disagreementFlag: false, lastUpdated: now, canInfluenceExecution: true,
    },
    {
      agentName: 'Beginner Translator Agent', confidence: 0.9, evidence: [candle.beginnerExplanation], bias: 'NEUTRAL', recommendation: 'Explain the market state before any action.', riskFlag: false, disagreementFlag: false, lastUpdated: now, canInfluenceExecution: false,
    },
  ];
};

const buildDecision = (candle: CandleTruthPacket, agents: AgentAnalysis[], marketState: MarketState): VerdictDecision => {
  const bullishVotes = agents.filter((agent) => agent.bias === 'BULLISH').length;
  const bearishVotes = agents.filter((agent) => agent.bias === 'BEARISH').length;
  const disagreement = Math.abs(bullishVotes - bearishVotes) < 2 ? 0.38 : 0.18;
  const direction: Direction = bullishVotes > bearishVotes ? 'LONG' : bearishVotes > bullishVotes ? 'SHORT' : 'NEUTRAL';
  const volatilityCost = clamp((candle.high - candle.low) / 42);
  const spreadCost = clamp(0.04 + candle.toxicity * 0.18);
  const slippageCost = clamp(0.06 + candle.manipulationRisk * 0.22);
  const marketImpact = clamp((candle.structuralVoid ? 0.72 : 0.12) + candle.volume / 60000);
  const liquidityRisk = clamp(candle.structuralVoid ? 0.74 : 0.18 + candle.toxicity * 0.42);
  const replaySimilarity = clamp(marketState.replaySync - candle.manipulationRisk * 0.18 + candle.trustScore * 0.08);
  const expectedEdge = candle.trustScore * 1.9 - volatilityCost * 0.42 - slippageCost - candle.manipulationRisk * 0.7;
  const robustLowerBound = expectedEdge - disagreement * 0.9 - (marketState.eventRisk === 'MEDIUM' ? 0.16 : 0);
  const hardLockReasons: string[] = [];
  if (candle.verdict === 'HARD_LOCK') hardLockReasons.push('Candle truth packet declared hard lock.');
  if (robustLowerBound < 0) hardLockReasons.push('Robust lower bound is negative.');
  if (candle.manipulationRisk > 0.7) hardLockReasons.push('Manipulation risk is too high.');
  const verdict: VerdictLabel = hardLockReasons.length > 0 ? 'HARD_LOCK' : candle.verdict === 'EXECUTE' && direction !== 'NEUTRAL' ? 'EXECUTE' : candle.verdict;
  const invalidation = direction === 'SHORT' ? candle.vah : candle.val;
  const targetBase = direction === 'SHORT' ? candle.close - (candle.high - candle.low) * 0.7 : candle.close + (candle.high - candle.low) * 0.7;
  return {
    verdict,
    direction,
    confidence: clamp(candle.trustScore * 0.68 + agents.reduce((sum, agent) => sum + agent.confidence, 0) / agents.length * 0.32 - disagreement * 0.2),
    reason: verdict === 'EXECUTE' ? 'Evidence is accepted, costs are inside limits, and the risk governor allows paper execution.' : verdict === 'WAIT' ? 'The idea is not proven yet; wait for acceptance and replay confirmation.' : verdict === 'EXPLICIT_ABSTAIN' ? 'Evidence is too weak or noisy; abstaining protects capital.' : 'Execution disabled by hard risk constraints.',
    beginnerReason: verdict === 'EXECUTE' ? 'The market gave enough proof to plan a paper trade.' : verdict === 'WAIT' ? 'Wait. One more proof point is needed.' : verdict === 'EXPLICIT_ABSTAIN' ? 'Do not trade. The market is messy.' : 'Hard lock. The system is protecting you.',
    expertReason: `${agents.length} agents voted; disagreement ${pct(disagreement)}, replay ${pct(replaySimilarity)}, robust lower bound ${expectedEdge.toFixed(2)}R → ${robustLowerBound.toFixed(2)}R.`,
    requiredConfirmation: direction === 'SHORT' ? `Reject below ${fmt(candle.poc)} and hold beneath VAH ${fmt(candle.vah)}.` : `Accept above POC ${fmt(candle.poc)} and defend VAL ${fmt(candle.val)}.`,
    invalidation,
    targets: [targetBase, direction === 'SHORT' ? targetBase - 9.5 : targetBase + 9.5],
    maxRisk: Math.abs(candle.close - invalidation) * 2,
    executionStyle: verdict === 'EXECUTE' ? 'Passive limit entry, reduce on toxicity spike, kill switch below invalidation.' : 'No execution route.',
    hardLockReasons,
    expectedEdge,
    volatilityCost,
    spreadCost,
    slippageCost,
    marketImpact,
    liquidityRisk,
    driftDistrust: clamp(0.1 + candle.toxicity * 0.32),
    modelDisagreement: disagreement,
    replaySimilarity,
    robustLowerBound,
    riskReward: Math.abs(targetBase - candle.close) / Math.max(Math.abs(candle.close - invalidation), 0.1),
  };
};

const buildLedger = (candle: CandleTruthPacket, agents: AgentAnalysis[], decision: VerdictDecision): LedgerEvent[] => {
  const votes = agents.map((agent) => `${agent.agentName}:${agent.bias}:${pct(agent.confidence)}`);
  const evidenceUsed = [`trust=${pct(candle.trustScore)}`, `toxicity=${pct(candle.toxicity)}`, `poc=${fmt(candle.poc)}`, `replay=${pct(decision.replaySimilarity)}`];
  return Array.from({ length: 5 }, (_, index) => ({
    eventId: `TL-${hashText(`${candle.id}-${index}`)}`,
    candleId: candle.id,
    timestamp: index === 0 ? candle.timestamp : `T+${index * 2}`,
    dataChecksum: hashText(`${candle.id}-${candle.volume}-${candle.delta}-${index}`),
    modelVersion: 'wraith-mock-0.1',
    ruleVersion: 'legal-risk-governor-v1',
    evidenceUsed,
    agentVotes: votes,
    confidenceBeforeDecision: clamp(decision.confidence - index * 0.03),
    verdict: decision.verdict,
    outcomeAfterNCandles: index === 0 ? 'pending replay mark' : index % 2 === 0 ? 'held inside expected path' : 'tested cancellation boundary',
    promotedStatus: decision.verdict === 'EXECUTE' && index > 2 ? 'promoted' : decision.verdict === 'HARD_LOCK' ? 'rejected' : 'held',
    replayHash: `R-${hashText(`${decision.reason}-${index}`)}`,
    humanOverride: 'none',
    riskGovernorStatus: decision.hardLockReasons.length > 0 ? 'blocked' : 'passed',
  }));
};

const buildScenarios = (candle: CandleTruthPacket, decision: VerdictDecision): Scenario[] => [
  {
    name: 'Likely path', probability: candle.continuationProbability,
    path: decision.direction === 'SHORT' ? 'Reject POC → probe lower value → cover into target 1.' : 'Defend value → reclaim POC → expand toward target 1.',
    cancellation: decision.direction === 'SHORT' ? `Acceptance above ${fmt(candle.vah)}` : `Break and accept below ${fmt(candle.val)}`,
  },
  {
    name: 'Failure path', probability: candle.reversalProbability,
    path: decision.direction === 'SHORT' ? 'Buyers reclaim upper core and trap shorts.' : 'Sellers crack lower core and trap buyers.',
    cancellation: `Hard invalidate at ${fmt(decision.invalidation)}.`,
  },
  {
    name: 'Abstain path', probability: clamp(candle.toxicity + decision.modelDisagreement * 0.4),
    path: 'Evidence fragments; no clean auction acceptance forms.',
    cancellation: 'Reassess after two clean candles with lower toxicity.',
  },
];

function Panel({ title, accent, children }: { title: string; accent: 'cyan' | 'gold' | 'danger'; children: ReactNode }) {
  return <section className={`panel panel-${accent}`}><div className="panel-title"><span>{title}</span></div>{children}</section>;
}

function StatusPill({ label, value, wide, className }: { label: string; value: string; wide?: boolean; className?: string }) {
  return <div className={`status-pill ${wide ? 'wide' : ''} ${className ?? ''}`}><span>{label}</span><strong>{value}</strong></div>;
}

function ContextLine({ label, value }: { label: string; value: string }) {
  return <div className="context-line"><span>{label}</span><strong>{value}</strong></div>;
}

function Metric({ label, value, tone }: { label: string; value: string; tone: Tone }) {
  return <div className={`metric metric-${tone}`}><span>{label}</span><strong>{value}</strong></div>;
}

function ManipulationDetector({ candle }: { candle: CandleTruthPacket }) {
  const assessment = assessManipulation(candle);
  return (
    <Panel title="Manipulation Risk" accent="danger">
      <div className="risk-head"><span className={classForRisk(assessment.level)}>{assessment.level}</span><span>{pct(assessment.score)}</span></div>
      <ul className="tight-list">{assessment.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
      <div className="action-pill">Recommended: {assessment.recommendedAction}</div>
    </Panel>
  );
}

function ExecutionLock({ risk, mode }: { risk: RiskState; mode: AutonomyMode }) {
  const liveText = risk.hardLockActive ? 'Execution disabled. Risk governor is fail-closed.' : mode === 'paper' ? 'Paper autonomy armed. Live trading remains locked.' : 'Manual observation mode. No autonomous routing.';
  return (
    <div className={`execution-lock ${risk.hardLockActive ? 'locked' : 'armed'}`}>
      <div className="lock-title">{risk.hardLockActive ? 'HARD LOCK' : mode === 'paper' ? 'PAPER AUTONOMY' : 'MANUAL SAFE'}</div>
      <div>{liveText}</div>
      {risk.locks.length > 0 && <ul>{risk.locks.map((lock) => <li key={lock}>{lock}</li>)}</ul>}
    </div>
  );
}

function RiskGovernor({ decision, marketState, mode }: { decision: VerdictDecision; marketState: MarketState; mode: AutonomyMode }) {
  const risk = evaluateRiskGovernor(decision, marketState);
  const gates: [string, boolean][] = [
    ['Daily max loss', risk.dailyMaxLossHit], ['Data stale', risk.staleData], ['Spread wide', risk.spreadTooWide], ['Thin liquidity', risk.liquidityInsufficient], ['Event risk', risk.eventRiskHigh], ['Model split', risk.modelDisagreementHigh], ['Manipulation', risk.manipulationRiskHigh], ['Lower bound', risk.robustLowerBoundNegative], ['Replay weak', risk.replaySimilarityWeak],
  ];
  return (
    <Panel title="Risk Governor" accent={risk.hardLockActive ? 'danger' : 'gold'}>
      <div className="governor-grid">{gates.map(([label, active]) => <div key={label} className={`gate ${active ? 'gate-closed' : 'gate-open'}`}><span>{label}</span><strong>{active ? 'LOCK' : 'PASS'}</strong></div>)}</div>
      <ExecutionLock risk={risk} mode={mode} />
    </Panel>
  );
}

function CandleIntelligenceEngine({ candle, mode }: { candle: CandleTruthPacket; mode: ComprehensionMode }) {
  const lines = mode === 'beginner'
    ? [candle.beginnerExplanation, candle.trappedSide !== 'NONE' ? `${candle.trappedSide.toLowerCase()} may be trapped.` : 'No obvious trapped side.', `Invalidation is below ${fmt(candle.val)}.`]
    : [candle.expertExplanation, `Bid ${candle.bidVolume.toLocaleString()} / Ask ${candle.askVolume.toLocaleString()} / imbalance nodes ${candle.imbalanceLadder.length}.`, `Fair value gap: ${candle.fairValueGap ? 'yes' : 'no'}; structural void: ${candle.structuralVoid ? 'yes' : 'no'}.`];
  return (
    <Panel title="Candle Intelligence Engine" accent="cyan">
      <ul className="tight-list">{lines.map((line) => <li key={line}>{line}</li>)}</ul>
      <div className="packet-strip"><Metric label="Trust" value={pct(candle.trustScore)} tone="cyan" /><Metric label="Toxicity" value={pct(candle.toxicity)} tone="red" /><Metric label="Continuation" value={pct(candle.continuationProbability)} tone="green" /><Metric label="Reversal" value={pct(candle.reversalProbability)} tone="gold" /></div>
    </Panel>
  );
}

function VerdictEngine({ decision }: { decision: VerdictDecision }) {
  return (
    <Panel title="Decision Certificate" accent={decision.verdict === 'HARD_LOCK' ? 'danger' : 'gold'}>
      <div className="certificate"><div className={`verdict ${classForVerdict(decision.verdict)}`}>{decision.verdict.replace('_', ' ')}</div><div className="direction">{decision.direction} · {pct(decision.confidence)}</div><p>{decision.reason}</p></div>
      <div className="decision-grid"><Metric label="Expected edge" value={`${decision.expectedEdge.toFixed(2)}R`} tone="green" /><Metric label="Robust lower" value={`${decision.robustLowerBound.toFixed(2)}R`} tone={decision.robustLowerBound > 0 ? 'green' : 'red'} /><Metric label="Replay" value={pct(decision.replaySimilarity)} tone="cyan" /><Metric label="Model split" value={pct(decision.modelDisagreement)} tone={decision.modelDisagreement > 0.34 ? 'red' : 'gold'} /></div>
    </Panel>
  );
}

function BeginnerTranslator({ candle, decision }: { candle: CandleTruthPacket; decision: VerdictDecision }) {
  return (
    <Panel title="Beginner Explanation" accent="cyan">
      <div className="beginner-copy">{decision.beginnerReason}</div><p>{candle.beginnerExplanation}</p>
      <div className="what-next"><strong>What must happen next</strong><span>{decision.requiredConfirmation}</span></div>
      <div className="what-next danger-text"><strong>What cancels the idea</strong><span>Acceptance through invalidation at {fmt(decision.invalidation)} or toxicity rising above 70%.</span></div>
    </Panel>
  );
}

function ScenarioEngine({ scenarios }: { scenarios: Scenario[] }) {
  return <Panel title="Scenario Engine" accent="cyan"><div className="scenario-stack">{scenarios.map((scenario) => <div key={scenario.name} className="scenario-card"><div className="scenario-title"><span>{scenario.name}</span><strong>{pct(scenario.probability)}</strong></div><p>{scenario.path}</p><small>Cancel: {scenario.cancellation}</small></div>)}</div></Panel>;
}

function AgentCouncil({ agents }: { agents: AgentAnalysis[] }) {
  return (
    <Panel title="AI Agent Council" accent="gold">
      <div className="agent-grid">{agents.map((agent) => <div key={agent.agentName} className={`agent-card ${agent.riskFlag ? 'agent-risk' : ''}`}><div className="agent-head"><strong>{agent.agentName}</strong><span>{pct(agent.confidence)}</span></div><div className={`bias bias-${agent.bias.toLowerCase()}`}>{agent.bias}</div><p>{agent.recommendation}</p><small>{agent.evidence[0]} · {agent.lastUpdated}</small><div className="agent-foot"><span>{agent.canInfluenceExecution ? 'execution vote' : 'explain only'}</span><span>{agent.disagreementFlag ? 'disagrees' : 'aligned'}</span></div></div>)}</div>
    </Panel>
  );
}

function TruthLedger({ ledger }: { ledger: LedgerEvent[] }) {
  return <Panel title="Truth Ledger / Replay Proof" accent="cyan"><div className="ledger-table">{ledger.map((event) => <div key={event.eventId} className="ledger-row"><span>{event.eventId}</span><span>{event.dataChecksum}</span><span>{event.verdict.replace('_', ' ')}</span><span>{event.outcomeAfterNCandles}</span><span>{event.promotedStatus}</span><span>{event.riskGovernorStatus}</span></div>)}</div></Panel>;
}

function ReplayDiagnostics({ decision, ledger }: { decision: VerdictDecision; ledger: LedgerEvent[] }) {
  return <div className="diagnostic-strip"><Metric label="Replay similarity" value={pct(decision.replaySimilarity)} tone="cyan" /><Metric label="Outcome proof" value={ledger[0].replayHash} tone="gold" /><Metric label="Vol cost" value={pct(decision.volatilityCost)} tone="red" /><Metric label="Spread" value={pct(decision.spreadCost)} tone="red" /><Metric label="Slippage" value={pct(decision.slippageCost)} tone="red" /><Metric label="Impact" value={pct(decision.marketImpact)} tone="gold" /></div>;
}

function TopStatusRail({ marketState, decision, mode }: { marketState: MarketState; decision: VerdictDecision; mode: AutonomyMode }) {
  const executionMode = mode === 'paper' ? 'PAPER' : 'SIM';
  return (
    <header className="top-rail">
      <div className="brand-block"><span className="micro-label">WRAITH X-RAY // SINGULARITY</span><strong>AGI TRADING TERMINAL</strong><small>Autonomous quantitative intelligence</small></div>
      <StatusPill label="Symbol" value={marketState.symbol} /><StatusPill label="TF" value={marketState.timeframe} /><StatusPill label="Session" value={marketState.session} />
      <StatusPill label="State" value={marketState.regime} wide /><StatusPill label="Playbook" value={marketState.activePlaybook} wide /><StatusPill label="Risk" value={mode === 'paper' ? 'Paper governed' : 'Manual'} />
      <StatusPill label="Verdict" value={decision.verdict.replace('_', ' ')} className={classForVerdict(decision.verdict)} /><StatusPill label="Truth" value={pct(marketState.truthSync)} /><StatusPill label="Health" value={pct(marketState.systemHealth)} /><StatusPill label="Latency" value={`${marketState.dataLatencyMs}ms`} /><StatusPill label="Execution" value={decision.verdict === 'HARD_LOCK' ? 'LIVE LOCKED' : executionMode} />
    </header>
  );
}

function LeftContextRail({ marketState, candle, decision }: { marketState: MarketState; candle: CandleTruthPacket; decision: VerdictDecision }) {
  const modules = ['Market Intelligence', 'Order Flow X-Ray', 'Auction Intelligence', 'Liquidity Hunter', 'Risk Engine', 'Execution Engine', 'Narrative Reasoner', 'Scenario Simulator'];
  return <aside className="left-rail"><Panel title="System Architecture" accent="cyan"><div className="module-list">{modules.map((module) => <div key={module} className="module-row"><span>{module}</span><strong>ACTIVE</strong></div>)}</div></Panel><Panel title="Market Context" accent="cyan"><ContextLine label="Regime" value={marketState.regime} /><ContextLine label="HTF trend" value={marketState.higherTimeframeTrend} /><ContextLine label="Liquidity" value={candle.liquiditySweepHigh ? 'Buy-side swept' : candle.liquiditySweepLow ? 'Sell-side swept' : 'Balanced'} /><ContextLine label="Event risk" value={marketState.eventRisk} /><ContextLine label="Manipulation" value={pct(candle.manipulationRisk)} /></Panel><BeginnerTranslator candle={candle} decision={decision} /><Panel title="System Locks" accent="danger"><ul className="tight-list"><li>Live execution remains locked.</li><li>No guaranteed profit claims.</li><li>Hard abstain if proof weakens.</li><li>Legal intelligence only.</li></ul></Panel></aside>;
}

function XRayMarketField({ marketState, selectedId, setSelectedId, decision }: { marketState: MarketState; selectedId: string; setSelectedId: (id: string) => void; decision: VerdictDecision }) {
  const selected = marketState.candles.find((candle) => candle.id === selectedId) ?? marketState.candles[0];
  const minPrice = Math.min(...marketState.candles.map((candle) => candle.low));
  const maxPrice = Math.max(...marketState.candles.map((candle) => candle.high));
  const priceToY = (price: number) => 290 - ((price - minPrice) / Math.max(maxPrice - minPrice, 1)) * 250;
  const step = 820 / marketState.candles.length;
  const selectedIndex = marketState.candles.findIndex((candle) => candle.id === selected.id);
  const selectedX = 28 + selectedIndex * step;
  const maxProfileVolume = Math.max(...selected.internalProfile.map((level) => level.volume));
  const handleFieldClick = (event: MouseEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const viewX = ((event.clientX - bounds.left) / bounds.width) * 900;
    const candleIndex = Math.max(0, Math.min(marketState.candles.length - 1, Math.round((viewX - 28) / step)));
    setSelectedId(marketState.candles[candleIndex].id);
  };
  const linePath = marketState.candles.map((candle, index) => `${index === 0 ? 'M' : 'L'} ${28 + index * step} ${priceToY(candle.close)}`).join(' ');
  const likelyEnd = decision.direction === 'SHORT' ? decision.targets[0] : decision.targets[0];
  const failureEnd = decision.invalidation;
  const likelyPath = `M ${selectedX} ${priceToY(selected.close)} C 590 ${priceToY(selected.poc) - 20}, 650 ${priceToY(likelyEnd) - 30}, 795 ${priceToY(likelyEnd)}`;
  const failurePath = `M ${selectedX} ${priceToY(selected.close)} C 590 ${priceToY(selected.val) + 45}, 680 ${priceToY(failureEnd) + 55}, 800 ${priceToY(failureEnd)}`;
  return (
    <main className="xray-field">
      <div className="field-title"><div><span className="micro-label">Central X-Ray Market Field</span><strong>Panoramic IQ Candle Chart</strong></div><div className="legend"><span className="dot cyan" />truth <span className="dot gold" />value <span className="dot red" />danger</div></div>
      <div className="market-stage">
      <svg viewBox="0 0 900 340" className="market-svg" role="img" aria-label="X-ray candle market field" onClick={handleFieldClick}>
        <defs><linearGradient id="coreGlow" x1="0" x2="1"><stop offset="0" stopColor="#68e8ff" stopOpacity="0.05" /><stop offset="1" stopColor="#d8b76a" stopOpacity="0.16" /></linearGradient><filter id="softGlow"><feGaussianBlur stdDeviation="3" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
        <rect x="18" y="38" width="850" height="270" rx="22" fill="url(#coreGlow)" stroke="#1b3c49" />
        {[selected.vah, selected.poc, selected.val].map((price, index) => <g key={price}><line x1="24" x2="864" y1={priceToY(price)} y2={priceToY(price)} stroke={index === 1 ? '#d8b76a' : '#55d8f3'} strokeDasharray={index === 1 ? '0' : '8 9'} opacity="0.65" /><text x="34" y={priceToY(price) - 5} fill={index === 1 ? '#d8b76a' : '#55d8f3'} fontSize="10">{index === 0 ? 'VAH' : index === 1 ? 'POC' : 'VAL'} {fmt(price)}</text></g>)}
        <path d={linePath} fill="none" stroke="#7de9ff" strokeWidth="2.5" opacity="0.58" />
        <path d={likelyPath} fill="none" stroke="#6ee7b7" strokeWidth="2" strokeDasharray="8 10" className="path-animate" />
        <path d={failurePath} fill="none" stroke="#f97070" strokeWidth="2" strokeDasharray="5 10" className="path-animate reverse" />
        <g opacity="0.88">
          <text x="777" y="58" fill="#8beaff" fontSize="10">AUCTION PROFILE</text>
          {selected.internalProfile.map((level) => {
            const width = (level.volume / maxProfileVolume) * 72;
            const fill = level.price === selected.poc ? '#d8b76a' : level.price >= selected.poc ? '#2aa6bd' : '#c89218';
            return <rect key={level.price} x={790} y={priceToY(level.price) - 4} width={width} height="6" rx="3" fill={fill} opacity={level.price === selected.poc ? 0.95 : 0.62} />;
          })}
          <text x="790" y={priceToY(selected.poc) - 7} fill="#d8b76a" fontSize="9">POC {fmt(selected.poc)}</text>
          <text x="790" y={priceToY(selected.vah) - 7} fill="#6ee7b7" fontSize="9">VAH {fmt(selected.vah)}</text>
          <text x="790" y={priceToY(selected.val) + 13} fill="#f0b849" fontSize="9">VAL {fmt(selected.val)}</text>
        </g>
        {marketState.candles.map((candle, index) => {
          const x = 28 + index * step;
          const yOpen = priceToY(candle.open);
          const yClose = priceToY(candle.close);
          const yHigh = priceToY(candle.high);
          const yLow = priceToY(candle.low);
          const top = Math.min(yOpen, yClose);
          const height = Math.max(Math.abs(yClose - yOpen), 3);
          const selectedCandle = candle.id === selectedId;
          const color = candle.close >= candle.open ? '#77e9c1' : '#ef7777';
          return <g key={candle.id} onClick={() => setSelectedId(candle.id)} className="clickable-candle"><rect x={x - 10} y="40" width="20" height="266" fill="transparent" /><line x1={x} x2={x} y1={yHigh} y2={yLow} stroke={color} strokeWidth={selectedCandle ? 3 : 1.4} opacity="0.9" /><rect x={x - 6} y={top} width="12" height={height} rx="3" fill={color} opacity={selectedCandle ? 0.95 : 0.6} stroke={selectedCandle ? '#ffffff' : 'transparent'} />{candle.absorptionNodes.length > 2 && <circle cx={x} cy={priceToY(candle.poc)} r={selectedCandle ? 7 : 4} fill="#d8b76a" opacity="0.84" filter="url(#softGlow)" />}{(candle.liquiditySweepHigh || candle.liquiditySweepLow) && <path d={`M ${x - 7} ${candle.liquiditySweepHigh ? yHigh - 10 : yLow + 10} L ${x} ${candle.liquiditySweepHigh ? yHigh - 20 : yLow + 20} L ${x + 7} ${candle.liquiditySweepHigh ? yHigh - 10 : yLow + 10}`} fill="none" stroke="#d65cff" strokeWidth="2" />}</g>;
        })}
        <rect x="594" y="72" width="236" height="88" rx="16" fill="#050a12" stroke="#284552" opacity="0.92" />
        <text x="610" y="96" fill="#8beaff" fontSize="11">SELECTED MARKET TRUTH PACKET</text><text x="610" y="122" fill="#ffffff" fontSize="21" fontWeight="700">{selected.id} · {selected.verdict.replace('_', ' ')}</text><text x="610" y="145" fill="#9fb2c4" fontSize="12">Trap: {selected.trappedSide} · Trust {pct(selected.trustScore)} · Toxicity {pct(selected.toxicity)}</text>
      </svg>
      <div className="candle-hit-layer" aria-label="Candle click targets">{marketState.candles.map((candle, index) => {
        const x = 28 + index * step;
        return <button key={candle.id} type="button" className="candle-hit" style={{ left: `${((x - 10) / 900) * 100}%`, top: `${(40 / 340) * 100}%`, width: `${(20 / 900) * 100}%`, height: `${(266 / 340) * 100}%` }} aria-label={`Inspect ${candle.id}`} onClick={() => setSelectedId(candle.id)} />;
      })}</div>
      </div>
    </main>
  );
}

function IQCandle({ candle }: { candle: CandleTruthPacket }) {
  const min = candle.low;
  const max = candle.high;
  const priceToY = (price: number) => 420 - ((price - min) / Math.max(max - min, 1)) * 360;
  return (
    <svg viewBox="0 0 460 470" className="iq-candle-svg" role="img" aria-label="Exploded IQ candle capsule">
      <defs><linearGradient id="shell" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#061625" /><stop offset="0.5" stopColor="#0a2230" /><stop offset="1" stopColor="#04070d" /></linearGradient><radialGradient id="tox"><stop stopColor="#f05252" stopOpacity={candle.toxicity} /><stop offset="1" stopColor="#f05252" stopOpacity="0" /></radialGradient></defs>
      <rect x="0" y="0" width="460" height="470" rx="28" fill="#020409" /><ellipse cx="230" cy="236" rx="152" ry="210" fill="url(#tox)" opacity="0.25" /><rect x="183" y="50" width="94" height="370" rx="46" fill="url(#shell)" stroke="#6ce6ff" strokeWidth="2" />
      <rect x="194" y={priceToY(candle.vah)} width="72" height={Math.max(priceToY(candle.val) - priceToY(candle.vah), 8)} rx="18" fill="#d8b76a" opacity="0.18" stroke="#d8b76a" />
      <line x1="120" x2="340" y1={priceToY(candle.open)} y2={priceToY(candle.open)} stroke="#9fb2c4" strokeDasharray="4 8" /><line x1="120" x2="340" y1={priceToY(candle.close)} y2={priceToY(candle.close)} stroke="#ffffff" strokeWidth="2" /><line x1="142" x2="318" y1={priceToY(candle.poc)} y2={priceToY(candle.poc)} stroke="#d8b76a" strokeWidth="4" />
      {candle.priceLevels.map((level, index) => { const y = priceToY(level.price); const width = 10 + level.imbalance * 56; const x = level.askVolume >= level.bidVolume ? 238 : 222 - width; return <rect key={`${level.price}-${index}`} x={x} y={y - 4} width={width} height="8" rx="4" fill={level.askVolume >= level.bidVolume ? '#67e8f9' : '#ef7777'} opacity={0.35 + level.absorption * 0.44} />; })}
      {candle.absorptionNodes.map((level) => <circle key={`abs-${level.price}`} cx="314" cy={priceToY(level.price)} r="7" fill="#d8b76a" opacity="0.92" />)}{candle.imbalanceLadder.map((level) => <path key={`imb-${level.price}`} d={`M 146 ${priceToY(level.price)} L 168 ${priceToY(level.price) - 8} L 168 ${priceToY(level.price) + 8} Z`} fill="#d65cff" opacity="0.72" />)}
      <text x="30" y="48" fill="#8beaff" fontSize="11">OUTER PRICE SHELL</text><text x="298" y={priceToY(candle.high) + 4} fill="#9fb2c4" fontSize="11">HIGH {fmt(candle.high)}</text><text x="298" y={priceToY(candle.low) + 4} fill="#9fb2c4" fontSize="11">LOW {fmt(candle.low)}</text><text x="24" y={priceToY(candle.poc) + 4} fill="#d8b76a" fontSize="11">POC / AUCTION HEART</text><text x="24" y={priceToY(candle.close) - 8} fill="#ffffff" fontSize="11">CLOSE {fmt(candle.close)}</text><text x="28" y="430" fill="#fca5a5" fontSize="12">Toxicity halo · {pct(candle.toxicity)}</text><text x="248" y="430" fill="#6ee7b7" fontSize="12">Trust state · {pct(candle.trustScore)}</text>
    </svg>
  );
}

function IQCandleCapsule({ candle, decision, agents, ledger, mode }: { candle: CandleTruthPacket; decision: VerdictDecision; agents: AgentAnalysis[]; ledger: LedgerEvent[]; mode: ComprehensionMode }) {
  return <section className="capsule-orbit"><div className="orbit-panel left-orbit"><VerdictEngine decision={decision} /><CandleIntelligenceEngine candle={candle} mode={mode} /></div><div className="candle-stage"><div className="stage-header"><span className="micro-label">Flagship mode</span><h1>IQ Candle Capsule</h1><p>The candle is a Market Truth Packet, anatomically opened.</p></div><IQCandle candle={candle} /></div><div className="orbit-panel right-orbit"><AgentCouncil agents={agents.slice(0, 3)} /><TruthLedger ledger={ledger.slice(0, 3)} /></div></section>;
}

function SelectedCandleInspector({ candle, mode }: { candle: CandleTruthPacket; mode: ComprehensionMode }) {
  return <Panel title="Selected Candle Inspector" accent="cyan"><div className="inspector-grid"><Metric label="Open" value={fmt(candle.open)} tone="neutral" /><Metric label="High" value={fmt(candle.high)} tone="green" /><Metric label="Low" value={fmt(candle.low)} tone="red" /><Metric label="Close" value={fmt(candle.close)} tone="cyan" /><Metric label="Delta" value={candle.delta.toLocaleString()} tone={candle.delta >= 0 ? 'green' : 'red'} /><Metric label="CVD" value={candle.cumulativeDelta.toLocaleString()} tone="gold" /><Metric label="POC" value={fmt(candle.poc)} tone="gold" /><Metric label="Trap" value={candle.trappedSide} tone={candle.trappedSide === 'NONE' ? 'neutral' : 'red'} /></div><p>{mode === 'beginner' ? candle.beginnerExplanation : candle.expertExplanation}</p></Panel>;
}

function DecisionSpine({ candle, decision, mode }: { candle: CandleTruthPacket; decision: VerdictDecision; mode: ComprehensionMode }) {
  const executeItems = decision.verdict === 'EXECUTE'
    ? [['Entry zone', `${fmt(candle.val)} → ${fmt(candle.poc)}`], ['Trigger', decision.requiredConfirmation], ['Invalidation', fmt(decision.invalidation)], ['Target 1', fmt(decision.targets[0])], ['Target 2', fmt(decision.targets[1])], ['Max loss', `$${fmt(decision.maxRisk, 0)}`], ['Style', decision.executionStyle]]
    : decision.verdict === 'WAIT'
      ? [['Missing', 'Accepted proof candle'], ['Must confirm', decision.requiredConfirmation], ['Must hold', fmt(decision.invalidation)], ['Cancels', 'Toxicity expansion or failed replay']]
      : decision.verdict === 'EXPLICIT_ABSTAIN'
        ? [['Why not', decision.reason], ['Toxicity source', `${pct(candle.toxicity)} halo`], ['Missing evidence', 'Agent agreement and replay strength'], ['Reassess', 'After two clean candles']]
        : [['Execution disabled', 'HARD LOCK'], ['Violated constraints', decision.hardLockReasons.join(' ') || 'Risk governor lock'], ['Operator action', 'Stand down'], ['Reassess', 'Only after constraints clear']];
  return <aside className="decision-spine"><VerdictEngine decision={decision} /><Panel title="Execution Spine" accent={decision.verdict === 'HARD_LOCK' ? 'danger' : 'gold'}><div className="spine-metrics"><Metric label="Direction" value={decision.direction} tone="cyan" /><Metric label="Confidence" value={pct(decision.confidence)} tone="green" /><Metric label="Risk/Reward" value={decision.riskReward.toFixed(2)} tone="gold" /><Metric label="Max risk" value={`$${fmt(decision.maxRisk, 0)}`} tone="red" /></div><div className="spine-list">{executeItems.map(([label, value]) => <ContextLine key={label} label={label} value={value} />)}</div><p className="expert-reason">{mode === 'beginner' ? decision.beginnerReason : decision.expertReason}</p></Panel><ManipulationDetector candle={candle} /></aside>;
}

function ArchitectureSummary() {
  return <section className="architecture-summary"><Panel title="Architecture Summary" accent="cyan"><div className="arch-flow">{['MarketState', 'FeatureExtraction', 'AgentInput', 'AgentAnalysis', 'EvidenceBundle', 'VerdictContribution', 'FinalDecision'].map((step) => <span key={step}>{step}</span>)}</div><p>Mock adapters generate legal replay data; the candle engine converts it into Market Truth Packets; the agent council votes; the verdict engine combines evidence, cost, replay, and risk; the governor can abstain or hard-lock execution.</p></Panel></section>;
}

const brittlePoints: BrittlePoint[] = [
  { name: 'Mock data may look smarter than real data', whyItBreaks: 'Synthetic patterns can accidentally flatter the UI and hide feed noise.', technicalFix: 'Tag all mock data as simulation, add adapter conformance tests, replay real historical sessions before enabling decisions.' },
  { name: 'AI agents may hallucinate', whyItBreaks: 'A language model can invent evidence that the data did not prove.', technicalFix: 'Require every agent recommendation to cite typed EvidenceBundle IDs from the feature extractor; reject uncited claims.' },
  { name: 'Candles may over-explain random noise', whyItBreaks: 'Microstructure noise can masquerade as intent.', technicalFix: 'Gate explanations behind minimum volume, replay similarity, and multi-agent agreement thresholds.' },
  { name: 'Beginner mode may oversimplify risk', whyItBreaks: 'Plain English can feel like certainty.', technicalFix: 'Beginner translation must include invalidation, uncertainty, and abstain language on every decision.' },
  { name: 'Expert mode may overload the screen', whyItBreaks: 'Too many metrics can reduce decision quality.', technicalFix: 'Use progressive disclosure: summary first, then drill-down packets and ledger rows.' },
  { name: 'Autonomous execution can be dangerous', whyItBreaks: 'Automation can route orders during stale data or regime breaks.', technicalFix: 'Keep live locked, require signed decision certificates, and enforce risk-governor gates server-side.' },
  { name: 'Manipulation detection can false-positive', whyItBreaks: 'Legitimate liquidity gaps can resemble suspicious flow.', technicalFix: 'Report defensive risk levels only, pair each flag with evidence, and require human review above medium risk.' },
  { name: 'Replay can overfit', whyItBreaks: 'A similar past setup can fail under a new regime.', technicalFix: 'Use purged walk-forward replay, regime labels, failure cases, and expiration rules for promoted lessons.' },
  { name: 'Latency can break scalping assumptions', whyItBreaks: 'A good signal decays if data or order routing lags.', technicalFix: 'Track feed age, decision age, route latency, and auto-hard-lock when latency exceeds strategy tolerance.' },
  { name: 'Market regimes can change suddenly', whyItBreaks: 'The best playbook can become invalid in one event candle.', technicalFix: 'Run continuous regime detection and force WAIT/HARD_LOCK during event risk or detected transition.' },
  { name: 'Legal boundaries must remain hard-coded', whyItBreaks: 'A flexible AI system could suggest prohibited behavior if not constrained.', technicalFix: 'Encode a non-bypassable policy layer blocking manipulation, front-running, spoofing, wash trading, and profit guarantees.' },
];

function BrittlePoints() {
  return <section className="brittle-section"><Panel title="Brittle Points → Concrete Fixes" accent="danger"><div className="brittle-grid">{brittlePoints.map((point) => <div key={point.name} className="brittle-card"><strong>{point.name}</strong><p>{point.whyItBreaks}</p><span>{point.technicalFix}</span></div>)}</div></Panel></section>;
}

function TerminalShell() {
  const marketState = useMemo(() => DataAdapterMock(), []);
  const [selectedId, setSelectedId] = useState(marketState.candles[19].id);
  const [terminalMode, setTerminalMode] = useState<TerminalMode>('capsule');
  const [comprehensionMode, setComprehensionMode] = useState<ComprehensionMode>('beginner');
  const [autonomyMode, setAutonomyMode] = useState<AutonomyMode>('manual');
  const selectedCandle = marketState.candles.find((candle) => candle.id === selectedId) ?? marketState.candles[0];
  const agents = useMemo(() => buildAgents(selectedCandle, marketState), [marketState, selectedCandle]);
  const decision = useMemo(() => buildDecision(selectedCandle, agents, marketState), [selectedCandle, agents, marketState]);
  const ledger = useMemo(() => buildLedger(selectedCandle, agents, decision), [selectedCandle, agents, decision]);
  const scenarios = useMemo(() => buildScenarios(selectedCandle, decision), [selectedCandle, decision]);
  return (
    <div className="wraith-shell">
      <TopStatusRail marketState={marketState} decision={decision} mode={autonomyMode} />
      <div className="control-deck"><button type="button" onClick={() => setTerminalMode(terminalMode === 'capsule' ? 'command' : 'capsule')}>{terminalMode === 'capsule' ? 'Switch to X-Ray Command Terminal' : 'Switch to IQ Candle Capsule'}</button><button type="button" onClick={() => setComprehensionMode(comprehensionMode === 'beginner' ? 'expert' : 'beginner')}>{comprehensionMode === 'beginner' ? 'Beginner Layer' : 'Expert Evidence Layer'}</button><button type="button" onClick={() => setAutonomyMode(autonomyMode === 'manual' ? 'paper' : 'manual')}>{autonomyMode === 'manual' ? 'Manual Mode' : 'Paper Autonomous Mode'}</button></div>
      {terminalMode === 'capsule' ? <IQCandleCapsule candle={selectedCandle} decision={decision} agents={agents} ledger={ledger} mode={comprehensionMode} /> : <div className="terminal-grid"><LeftContextRail marketState={marketState} candle={selectedCandle} decision={decision} /><div className="center-stack"><XRayMarketField marketState={marketState} selectedId={selectedId} setSelectedId={setSelectedId} decision={decision} /><ReplayDiagnostics decision={decision} ledger={ledger} /><div className="lower-grid"><SelectedCandleInspector candle={selectedCandle} mode={comprehensionMode} /><ScenarioEngine scenarios={scenarios} /><RiskGovernor decision={decision} marketState={marketState} mode={autonomyMode} /></div><AgentCouncil agents={agents} /><TruthLedger ledger={ledger} /></div><DecisionSpine candle={selectedCandle} decision={decision} mode={comprehensionMode} /></div>}
      {terminalMode === 'capsule' && <div className="capsule-bottom"><SelectedCandleInspector candle={selectedCandle} mode={comprehensionMode} /><ScenarioEngine scenarios={scenarios} /><RiskGovernor decision={decision} marketState={marketState} mode={autonomyMode} /><ReplayDiagnostics decision={decision} ledger={ledger} /></div>}
      <ArchitectureSummary /><BrittlePoints />
    </div>
  );
}

function App() {
  return <><style>{styles}</style><TerminalShell /></>;
}

const styles = `
:root { color-scheme: dark; background: #020409; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
* { box-sizing: border-box; }
body { margin: 0; background: radial-gradient(circle at 50% 0%, #0a1a29 0%, #020409 42%, #000 100%); color: #e5f7ff; }
button { border: 1px solid rgba(104, 232, 255, 0.28); background: linear-gradient(180deg, rgba(16, 35, 48, 0.96), rgba(4, 9, 16, 0.96)); color: #e8fbff; border-radius: 999px; padding: 10px 16px; font-weight: 700; letter-spacing: 0.02em; cursor: pointer; box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 14px 40px rgba(0,0,0,0.32); }
button:hover { border-color: rgba(216, 183, 106, 0.75); transform: translateY(-1px); }
.wraith-shell { min-height: 100vh; padding: 14px; background-image: linear-gradient(rgba(104,232,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(104,232,255,0.025) 1px, transparent 1px); background-size: 44px 44px; }
.top-rail { display: grid; grid-template-columns: 1.3fr repeat(11, minmax(84px, auto)); gap: 8px; align-items: stretch; margin-bottom: 10px; }
.brand-block, .status-pill, .panel { border: 1px solid rgba(104, 232, 255, 0.16); background: linear-gradient(180deg, rgba(9, 18, 30, 0.92), rgba(3, 7, 13, 0.95)); box-shadow: inset 0 1px 0 rgba(255,255,255,0.045), 0 16px 50px rgba(0,0,0,0.35); backdrop-filter: blur(18px); }
.brand-block { border-radius: 18px; padding: 12px 14px; }
.brand-block strong { display: block; font-size: 14px; letter-spacing: 0.12em; }
.brand-block small { display: block; margin-top: 6px; color: #7f93a7; font-size: 9px; letter-spacing: 0.16em; text-transform: uppercase; }
.micro-label { display: block; color: #68e8ff; font-size: 10px; text-transform: uppercase; letter-spacing: 0.18em; margin-bottom: 4px; }
.status-pill { border-radius: 14px; padding: 10px; min-width: 84px; overflow: hidden; }
.status-pill.wide { min-width: 170px; }
.status-pill span, .metric span, .context-line span { display: block; color: #74879a; font-size: 10px; text-transform: uppercase; letter-spacing: 0.12em; }
.status-pill strong { display: block; margin-top: 4px; color: #f5fbff; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.control-deck { display: flex; gap: 10px; justify-content: center; margin: 12px 0; }
.terminal-grid { display: grid; grid-template-columns: minmax(260px, 0.75fr) minmax(620px, 2fr) minmax(280px, 0.85fr); gap: 12px; align-items: start; }
.left-rail, .decision-spine, .center-stack, .orbit-panel { display: grid; gap: 12px; }
.lower-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.panel { position: relative; border-radius: 22px; padding: 14px; overflow: hidden; }
.panel:before { content: ''; position: absolute; inset: 0; border-radius: inherit; pointer-events: none; background: radial-gradient(circle at top right, rgba(104,232,255,0.1), transparent 42%); }
.panel-gold { border-color: rgba(216, 183, 106, 0.25); }
.panel-danger { border-color: rgba(249, 112, 112, 0.3); }
.panel-title { position: relative; display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; color: #ecfbff; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; font-size: 11px; }
.panel-title:after { content: ''; flex: 1; height: 1px; margin-left: 12px; background: linear-gradient(90deg, rgba(104,232,255,0.4), transparent); }
.xray-field { border-radius: 26px; border: 1px solid rgba(104,232,255,0.18); background: radial-gradient(circle at 50% 10%, rgba(104,232,255,0.09), rgba(4,8,14,0.96) 46%); padding: 16px; box-shadow: 0 24px 80px rgba(0,0,0,0.48); }
.field-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.field-title strong { font-size: 18px; letter-spacing: 0.06em; }
.legend { color: #8fa1b4; font-size: 11px; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin: 0 5px 0 12px; }
.cyan { background: #68e8ff; } .gold { background: #d8b76a; } .red { background: #f97070; }
.market-stage { position: relative; }
.market-svg { width: 100%; height: auto; display: block; }
.candle-hit-layer { position: absolute; inset: 0; z-index: 2; }
.candle-hit { position: absolute; padding: 0; border: 0; border-radius: 0; background: transparent; box-shadow: none; }
.candle-hit:hover { background: rgba(104,232,255,0.08); transform: none; }
.clickable-candle { cursor: pointer; transition: opacity 180ms ease; }
.clickable-candle:hover { opacity: 0.72; }
.module-list { display: grid; gap: 7px; }
.module-row { display: flex; justify-content: space-between; align-items: center; padding: 7px 8px; border-radius: 10px; background: rgba(255,255,255,0.035); color: #a9bacb; font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; }
.module-row strong { color: #6ee7b7; font-size: 10px; }
.path-animate { stroke-dashoffset: 160; animation: flowPath 3.5s linear infinite; }
.path-animate.reverse { animation-direction: reverse; }
@keyframes flowPath { to { stroke-dashoffset: 0; } }
.diagnostic-strip, .packet-strip, .decision-grid, .spine-metrics, .inspector-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.metric { border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.035); border-radius: 14px; padding: 10px; min-height: 58px; }
.metric strong { display: block; margin-top: 5px; font-size: 15px; overflow-wrap: anywhere; }
.metric-cyan strong, .state-wait { color: #68e8ff; } .metric-green strong, .state-positive { color: #6ee7b7; } .metric-gold strong { color: #d8b76a; } .metric-red strong, .state-danger { color: #f97070; } .state-lock { color: #ff4d4d; }
.context-line { display: grid; grid-template-columns: 0.42fr 1fr; gap: 8px; align-items: baseline; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
.context-line strong { color: #e8faff; font-size: 12px; }
.tight-list { margin: 0; padding-left: 18px; color: #b8c8d8; line-height: 1.45; }
.beginner-copy { color: #ffffff; font-size: 18px; line-height: 1.25; margin-bottom: 8px; }
.what-next { display: grid; gap: 5px; margin-top: 10px; padding: 10px; border: 1px solid rgba(104,232,255,0.13); border-radius: 14px; background: rgba(104,232,255,0.04); }
.danger-text { color: #fca5a5; border-color: rgba(249,112,112,0.18); background: rgba(249,112,112,0.04); }
.certificate .verdict { font-size: 26px; font-weight: 900; letter-spacing: 0.08em; }
.certificate .direction { color: #d8b76a; font-weight: 800; margin-top: 4px; }
.certificate p, .panel p { color: #b7c8d9; line-height: 1.5; }
.governor-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.gate { display: flex; justify-content: space-between; gap: 8px; padding: 9px; border-radius: 12px; background: rgba(255,255,255,0.035); color: #a9bacb; font-size: 12px; }
.gate-open strong { color: #6ee7b7; } .gate-closed strong { color: #f97070; }
.execution-lock { margin-top: 10px; padding: 12px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); }
.execution-lock.locked { background: repeating-linear-gradient(135deg, rgba(249,112,112,0.16), rgba(249,112,112,0.16) 8px, rgba(10,10,10,0.2) 8px, rgba(10,10,10,0.2) 16px); }
.execution-lock.armed { background: rgba(110,231,183,0.07); }
.lock-title { font-weight: 900; letter-spacing: 0.12em; margin-bottom: 5px; }
.risk-head, .scenario-title, .agent-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-weight: 800; }
.action-pill { display: inline-block; margin-top: 10px; padding: 8px 10px; border-radius: 999px; color: #f7e4af; background: rgba(216,183,106,0.1); border: 1px solid rgba(216,183,106,0.22); font-size: 12px; text-transform: uppercase; }
.scenario-stack, .agent-grid, .brittle-grid { display: grid; gap: 10px; }
.scenario-card, .agent-card, .brittle-card { border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.035); border-radius: 16px; padding: 12px; }
.scenario-card small, .agent-card small, .brittle-card span { color: #8fb7c7; }
.agent-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.agent-card p { margin: 8px 0; font-size: 12px; }
.agent-risk { border-color: rgba(249,112,112,0.3); }
.bias { display: inline-flex; margin-top: 8px; padding: 4px 8px; border-radius: 999px; font-size: 10px; font-weight: 900; }
.bias-bullish { color: #6ee7b7; background: rgba(110,231,183,0.08); } .bias-bearish { color: #f97070; background: rgba(249,112,112,0.08); } .bias-neutral { color: #d8b76a; background: rgba(216,183,106,0.08); }
.agent-foot { display: flex; justify-content: space-between; margin-top: 8px; color: #72869a; font-size: 10px; text-transform: uppercase; }
.ledger-table { display: grid; gap: 6px; }
.ledger-row { display: grid; grid-template-columns: 1fr 0.9fr 0.9fr 1.4fr 0.7fr 0.7fr; gap: 8px; padding: 8px; border-radius: 10px; background: rgba(255,255,255,0.035); color: #9fb2c4; font-size: 11px; }
.capsule-orbit { display: grid; grid-template-columns: minmax(280px, 0.9fr) minmax(460px, 1.2fr) minmax(280px, 0.9fr); gap: 14px; align-items: center; max-width: 1560px; margin: 0 auto; }
.candle-stage { min-height: 680px; display: grid; place-items: center; border-radius: 34px; border: 1px solid rgba(104,232,255,0.2); background: radial-gradient(circle at 50% 46%, rgba(104,232,255,0.16), rgba(5,9,15,0.95) 52%, rgba(0,0,0,0.98)); box-shadow: 0 34px 100px rgba(0,0,0,0.55); padding: 20px; }
.stage-header { text-align: center; align-self: end; }
.stage-header h1 { margin: 0; font-size: clamp(32px, 5vw, 64px); letter-spacing: 0.06em; }
.stage-header p { color: #b7c8d9; margin: 8px 0 0; }
.iq-candle-svg { width: min(100%, 560px); filter: drop-shadow(0 0 45px rgba(104,232,255,0.14)); }
.capsule-bottom { max-width: 1560px; margin: 14px auto 0; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.capsule-bottom .diagnostic-strip { grid-column: 1 / -1; }
.architecture-summary, .brittle-section { margin-top: 14px; }
.arch-flow { display: flex; flex-wrap: wrap; gap: 8px; }
.arch-flow span { padding: 8px 10px; border-radius: 999px; background: rgba(104,232,255,0.06); border: 1px solid rgba(104,232,255,0.18); color: #bff5ff; font-size: 12px; }
.brittle-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.brittle-card strong { color: #fff; display: block; margin-bottom: 6px; }
.brittle-card p { font-size: 12px; margin: 0 0 8px; }
.expert-reason { font-size: 12px; }
@media (max-width: 1280px) { .top-rail, .terminal-grid, .capsule-orbit, .capsule-bottom, .lower-grid { grid-template-columns: 1fr; } .agent-grid, .brittle-grid { grid-template-columns: 1fr; } .status-pill.wide { min-width: 0; } }
@media (max-width: 760px) { .diagnostic-strip, .packet-strip, .decision-grid, .spine-metrics, .inspector-grid, .governor-grid { grid-template-columns: 1fr 1fr; } .control-deck { flex-direction: column; } .ledger-row { grid-template-columns: 1fr; } }
`;

export default App;
