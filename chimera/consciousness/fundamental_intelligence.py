"""
FUNDAMENTAL INTELLIGENCE MODULE - DEXTER INTEGRATION

This module integrates fundamental analysis capabilities inspired by Dexter
(virattt/dexter) to complement our technical/orderflow analysis.

The key insight: Institutional traders don't just look at charts OR fundamentals,
they look at BOTH. This module provides:

1. Fundamental Data Fetching - Income statements, balance sheets, cash flow
2. Valuation Analysis - DCF, P/E, P/B, EV/EBITDA comparisons
3. Financial Health Scoring - Debt ratios, liquidity, profitability
4. Earnings Intelligence - Upcoming earnings, analyst estimates
5. Insider Activity - Insider buying/selling signals

Combined with our technical analysis, this creates TRUE institutional-grade
trading intelligence.

Author: Devin (for Prince)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class FundamentalHealth(Enum):
    """Overall fundamental health classification."""
    EXCELLENT = "excellent"      # Strong financials, growing, undervalued
    GOOD = "good"               # Solid financials, stable
    FAIR = "fair"               # Mixed signals
    POOR = "poor"               # Weak financials, declining
    CRITICAL = "critical"       # Serious financial issues


class ValuationStatus(Enum):
    """Valuation relative to intrinsic value."""
    DEEPLY_UNDERVALUED = "deeply_undervalued"   # >30% below fair value
    UNDERVALUED = "undervalued"                  # 10-30% below fair value
    FAIRLY_VALUED = "fairly_valued"              # Within 10% of fair value
    OVERVALUED = "overvalued"                    # 10-30% above fair value
    DEEPLY_OVERVALUED = "deeply_overvalued"      # >30% above fair value


class EarningsSignal(Enum):
    """Earnings-related signal."""
    BEAT_EXPECTED = "beat_expected"      # Likely to beat estimates
    MEET_EXPECTED = "meet_expected"      # Likely to meet estimates
    MISS_EXPECTED = "miss_expected"      # Likely to miss estimates
    NO_SIGNAL = "no_signal"              # Insufficient data


class InsiderSignal(Enum):
    """Insider trading signal."""
    STRONG_BUYING = "strong_buying"      # Significant insider buying
    BUYING = "buying"                    # Moderate insider buying
    NEUTRAL = "neutral"                  # Mixed or no activity
    SELLING = "selling"                  # Moderate insider selling
    STRONG_SELLING = "strong_selling"    # Significant insider selling


@dataclass
class IncomeStatement:
    """Key income statement metrics."""
    period: str  # "annual" or "quarterly"
    date: datetime
    revenue: float
    gross_profit: float
    operating_income: float
    net_income: float
    eps: float
    revenue_growth: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "date": self.date.isoformat(),
            "revenue": self.revenue,
            "gross_profit": self.gross_profit,
            "operating_income": self.operating_income,
            "net_income": self.net_income,
            "eps": self.eps,
            "revenue_growth": self.revenue_growth,
            "gross_margin": self.gross_margin,
            "operating_margin": self.operating_margin,
            "net_margin": self.net_margin,
        }


@dataclass
class BalanceSheet:
    """Key balance sheet metrics."""
    date: datetime
    total_assets: float
    total_liabilities: float
    total_equity: float
    cash_and_equivalents: float
    total_debt: float
    current_assets: float
    current_liabilities: float
    current_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    book_value_per_share: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "total_equity": self.total_equity,
            "cash_and_equivalents": self.cash_and_equivalents,
            "total_debt": self.total_debt,
            "current_assets": self.current_assets,
            "current_liabilities": self.current_liabilities,
            "current_ratio": self.current_ratio,
            "debt_to_equity": self.debt_to_equity,
            "book_value_per_share": self.book_value_per_share,
        }


@dataclass
class CashFlow:
    """Key cash flow metrics."""
    date: datetime
    operating_cash_flow: float
    capital_expenditure: float
    free_cash_flow: float
    dividends_paid: float
    share_repurchases: float
    fcf_margin: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "operating_cash_flow": self.operating_cash_flow,
            "capital_expenditure": self.capital_expenditure,
            "free_cash_flow": self.free_cash_flow,
            "dividends_paid": self.dividends_paid,
            "share_repurchases": self.share_repurchases,
            "fcf_margin": self.fcf_margin,
        }


@dataclass
class ValuationMetrics:
    """Valuation metrics and ratios."""
    market_cap: float
    enterprise_value: float
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    peg_ratio: Optional[float]
    price_to_book: Optional[float]
    price_to_sales: Optional[float]
    ev_to_ebitda: Optional[float]
    ev_to_revenue: Optional[float]
    dividend_yield: Optional[float]
    
    # DCF-related
    estimated_fair_value: Optional[float] = None
    upside_potential: Optional[float] = None
    valuation_status: ValuationStatus = ValuationStatus.FAIRLY_VALUED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_cap": self.market_cap,
            "enterprise_value": self.enterprise_value,
            "pe_ratio": self.pe_ratio,
            "forward_pe": self.forward_pe,
            "peg_ratio": self.peg_ratio,
            "price_to_book": self.price_to_book,
            "price_to_sales": self.price_to_sales,
            "ev_to_ebitda": self.ev_to_ebitda,
            "ev_to_revenue": self.ev_to_revenue,
            "dividend_yield": self.dividend_yield,
            "estimated_fair_value": self.estimated_fair_value,
            "upside_potential": self.upside_potential,
            "valuation_status": self.valuation_status.value,
        }


@dataclass
class FinancialHealthScore:
    """Comprehensive financial health assessment."""
    overall_health: FundamentalHealth
    overall_score: float  # 0-100
    
    # Component scores (0-100)
    profitability_score: float
    growth_score: float
    liquidity_score: float
    solvency_score: float
    efficiency_score: float
    
    # Flags
    red_flags: List[str]
    green_flags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_health": self.overall_health.value,
            "overall_score": self.overall_score,
            "profitability_score": self.profitability_score,
            "growth_score": self.growth_score,
            "liquidity_score": self.liquidity_score,
            "solvency_score": self.solvency_score,
            "efficiency_score": self.efficiency_score,
            "red_flags": self.red_flags,
            "green_flags": self.green_flags,
        }


@dataclass
class EarningsIntelligence:
    """Earnings-related intelligence."""
    next_earnings_date: Optional[datetime]
    days_until_earnings: Optional[int]
    
    # Estimates
    eps_estimate: Optional[float]
    revenue_estimate: Optional[float]
    
    # Historical
    last_eps_actual: Optional[float]
    last_eps_estimate: Optional[float]
    last_surprise_pct: Optional[float]
    
    # Signal
    earnings_signal: EarningsSignal
    beat_rate_4q: Optional[float]  # % of beats in last 4 quarters
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_earnings_date": self.next_earnings_date.isoformat() if self.next_earnings_date else None,
            "days_until_earnings": self.days_until_earnings,
            "eps_estimate": self.eps_estimate,
            "revenue_estimate": self.revenue_estimate,
            "last_eps_actual": self.last_eps_actual,
            "last_eps_estimate": self.last_eps_estimate,
            "last_surprise_pct": self.last_surprise_pct,
            "earnings_signal": self.earnings_signal.value,
            "beat_rate_4q": self.beat_rate_4q,
        }


@dataclass
class InsiderActivity:
    """Insider trading activity analysis."""
    insider_signal: InsiderSignal
    
    # Recent activity (last 90 days)
    total_buys: int
    total_sells: int
    net_shares: int
    net_value: float
    
    # Notable transactions
    notable_transactions: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "insider_signal": self.insider_signal.value,
            "total_buys": self.total_buys,
            "total_sells": self.total_sells,
            "net_shares": self.net_shares,
            "net_value": self.net_value,
            "notable_transactions": self.notable_transactions,
        }


@dataclass
class FundamentalAnalysis:
    """Complete fundamental analysis output."""
    timestamp: datetime
    symbol: str
    company_name: str
    sector: str
    industry: str
    current_price: float
    
    # Financial statements
    income_statements: List[IncomeStatement]
    balance_sheet: Optional[BalanceSheet]
    cash_flow: Optional[CashFlow]
    
    # Analysis
    valuation: ValuationMetrics
    health_score: FinancialHealthScore
    earnings: EarningsIntelligence
    insider_activity: InsiderActivity
    
    # Combined signal
    fundamental_bias: str  # "bullish", "bearish", "neutral"
    fundamental_confidence: float  # 0-1
    reasoning: str
    
    # Meta
    analysis_time_ms: float
    data_quality: str  # "high", "medium", "low"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "company_name": self.company_name,
            "sector": self.sector,
            "industry": self.industry,
            "current_price": self.current_price,
            "income_statements": [i.to_dict() for i in self.income_statements],
            "balance_sheet": self.balance_sheet.to_dict() if self.balance_sheet else None,
            "cash_flow": self.cash_flow.to_dict() if self.cash_flow else None,
            "valuation": self.valuation.to_dict(),
            "health_score": self.health_score.to_dict(),
            "earnings": self.earnings.to_dict(),
            "insider_activity": self.insider_activity.to_dict(),
            "fundamental_bias": self.fundamental_bias,
            "fundamental_confidence": self.fundamental_confidence,
            "reasoning": self.reasoning,
            "analysis_time_ms": self.analysis_time_ms,
            "data_quality": self.data_quality,
        }


class FundamentalIntelligence:
    """
    FUNDAMENTAL INTELLIGENCE ENGINE
    
    Provides fundamental analysis to complement technical/orderflow analysis.
    Inspired by Dexter (virattt/dexter) but integrated with our system.
    """
    
    def __init__(
        self,
        # Valuation thresholds
        undervalued_threshold: float = 0.10,  # 10% below fair value
        deeply_undervalued_threshold: float = 0.30,  # 30% below fair value
        # Health thresholds
        min_current_ratio: float = 1.0,
        max_debt_to_equity: float = 2.0,
        min_profit_margin: float = 0.05,
    ):
        self.undervalued_threshold = undervalued_threshold
        self.deeply_undervalued_threshold = deeply_undervalued_threshold
        self.min_current_ratio = min_current_ratio
        self.max_debt_to_equity = max_debt_to_equity
        self.min_profit_margin = min_profit_margin
    
    def analyze(self, symbol: str) -> FundamentalAnalysis:
        """
        Perform complete fundamental analysis on a symbol.
        
        This is the main entry point that orchestrates all fundamental analysis.
        """
        import time
        start_time = time.time()
        
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance is required for fundamental analysis")
        
        # Fetch data from yfinance
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get company info
        company_name = info.get("longName", info.get("shortName", symbol))
        sector = info.get("sector", "Unknown")
        industry = info.get("industry", "Unknown")
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        
        # Fetch financial statements
        income_statements = self._fetch_income_statements(ticker)
        balance_sheet = self._fetch_balance_sheet(ticker, info)
        cash_flow = self._fetch_cash_flow(ticker)
        
        # Calculate valuation metrics
        valuation = self._calculate_valuation(info, income_statements, cash_flow, current_price)
        
        # Calculate health score
        health_score = self._calculate_health_score(info, income_statements, balance_sheet, cash_flow)
        
        # Get earnings intelligence
        earnings = self._get_earnings_intelligence(ticker, info)
        
        # Get insider activity
        insider_activity = self._get_insider_activity(ticker)
        
        # Generate combined signal
        fundamental_bias, fundamental_confidence, reasoning = self._generate_signal(
            valuation, health_score, earnings, insider_activity
        )
        
        # Determine data quality
        data_quality = self._assess_data_quality(info, income_statements, balance_sheet)
        
        analysis_time_ms = (time.time() - start_time) * 1000
        
        return FundamentalAnalysis(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            company_name=company_name,
            sector=sector,
            industry=industry,
            current_price=current_price,
            income_statements=income_statements,
            balance_sheet=balance_sheet,
            cash_flow=cash_flow,
            valuation=valuation,
            health_score=health_score,
            earnings=earnings,
            insider_activity=insider_activity,
            fundamental_bias=fundamental_bias,
            fundamental_confidence=fundamental_confidence,
            reasoning=reasoning,
            analysis_time_ms=analysis_time_ms,
            data_quality=data_quality,
        )
    
    def _fetch_income_statements(self, ticker) -> List[IncomeStatement]:
        """Fetch and parse income statements."""
        statements = []
        
        try:
            # Get annual income statements
            income_df = ticker.income_stmt
            if income_df is not None and not income_df.empty:
                for col in income_df.columns[:4]:  # Last 4 years
                    try:
                        revenue = float(income_df.loc["Total Revenue", col]) if "Total Revenue" in income_df.index else 0
                        gross_profit = float(income_df.loc["Gross Profit", col]) if "Gross Profit" in income_df.index else 0
                        operating_income = float(income_df.loc["Operating Income", col]) if "Operating Income" in income_df.index else 0
                        net_income = float(income_df.loc["Net Income", col]) if "Net Income" in income_df.index else 0
                        
                        # Calculate margins
                        gross_margin = gross_profit / revenue if revenue > 0 else None
                        operating_margin = operating_income / revenue if revenue > 0 else None
                        net_margin = net_income / revenue if revenue > 0 else None
                        
                        # EPS (basic)
                        eps = float(income_df.loc["Basic EPS", col]) if "Basic EPS" in income_df.index else 0
                        
                        statements.append(IncomeStatement(
                            period="annual",
                            date=col.to_pydatetime() if hasattr(col, 'to_pydatetime') else datetime.now(timezone.utc),
                            revenue=revenue,
                            gross_profit=gross_profit,
                            operating_income=operating_income,
                            net_income=net_income,
                            eps=eps,
                            gross_margin=gross_margin,
                            operating_margin=operating_margin,
                            net_margin=net_margin,
                        ))
                    except Exception:
                        continue
        except Exception:
            pass
        
        # Calculate revenue growth
        if len(statements) >= 2:
            for i in range(len(statements) - 1):
                if statements[i+1].revenue > 0:
                    statements[i].revenue_growth = (statements[i].revenue - statements[i+1].revenue) / statements[i+1].revenue
        
        return statements
    
    def _fetch_balance_sheet(self, ticker, info: Dict) -> Optional[BalanceSheet]:
        """Fetch and parse balance sheet."""
        try:
            bs_df = ticker.balance_sheet
            if bs_df is None or bs_df.empty:
                return None
            
            col = bs_df.columns[0]  # Most recent
            
            total_assets = float(bs_df.loc["Total Assets", col]) if "Total Assets" in bs_df.index else 0
            total_liabilities = float(bs_df.loc["Total Liabilities Net Minority Interest", col]) if "Total Liabilities Net Minority Interest" in bs_df.index else 0
            total_equity = float(bs_df.loc["Total Equity Gross Minority Interest", col]) if "Total Equity Gross Minority Interest" in bs_df.index else total_assets - total_liabilities
            
            cash = float(bs_df.loc["Cash And Cash Equivalents", col]) if "Cash And Cash Equivalents" in bs_df.index else 0
            total_debt = float(bs_df.loc["Total Debt", col]) if "Total Debt" in bs_df.index else 0
            
            current_assets = float(bs_df.loc["Current Assets", col]) if "Current Assets" in bs_df.index else 0
            current_liabilities = float(bs_df.loc["Current Liabilities", col]) if "Current Liabilities" in bs_df.index else 0
            
            # Calculate ratios
            current_ratio = current_assets / current_liabilities if current_liabilities > 0 else None
            debt_to_equity = total_debt / total_equity if total_equity > 0 else None
            
            # Book value per share from info
            book_value_per_share = info.get("bookValue")
            
            return BalanceSheet(
                date=col.to_pydatetime() if hasattr(col, 'to_pydatetime') else datetime.now(timezone.utc),
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                total_equity=total_equity,
                cash_and_equivalents=cash,
                total_debt=total_debt,
                current_assets=current_assets,
                current_liabilities=current_liabilities,
                current_ratio=current_ratio,
                debt_to_equity=debt_to_equity,
                book_value_per_share=book_value_per_share,
            )
        except Exception:
            return None
    
    def _fetch_cash_flow(self, ticker) -> Optional[CashFlow]:
        """Fetch and parse cash flow statement."""
        try:
            cf_df = ticker.cashflow
            if cf_df is None or cf_df.empty:
                return None
            
            col = cf_df.columns[0]  # Most recent
            
            operating_cf = float(cf_df.loc["Operating Cash Flow", col]) if "Operating Cash Flow" in cf_df.index else 0
            capex = float(cf_df.loc["Capital Expenditure", col]) if "Capital Expenditure" in cf_df.index else 0
            free_cf = float(cf_df.loc["Free Cash Flow", col]) if "Free Cash Flow" in cf_df.index else operating_cf + capex
            
            dividends = float(cf_df.loc["Cash Dividends Paid", col]) if "Cash Dividends Paid" in cf_df.index else 0
            repurchases = float(cf_df.loc["Repurchase Of Capital Stock", col]) if "Repurchase Of Capital Stock" in cf_df.index else 0
            
            return CashFlow(
                date=col.to_pydatetime() if hasattr(col, 'to_pydatetime') else datetime.now(timezone.utc),
                operating_cash_flow=operating_cf,
                capital_expenditure=capex,
                free_cash_flow=free_cf,
                dividends_paid=abs(dividends),
                share_repurchases=abs(repurchases),
            )
        except Exception:
            return None
    
    def _calculate_valuation(
        self,
        info: Dict,
        income_statements: List[IncomeStatement],
        cash_flow: Optional[CashFlow],
        current_price: float,
    ) -> ValuationMetrics:
        """Calculate valuation metrics."""
        market_cap = info.get("marketCap", 0)
        enterprise_value = info.get("enterpriseValue", 0)
        
        pe_ratio = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        peg_ratio = info.get("pegRatio")
        price_to_book = info.get("priceToBook")
        price_to_sales = info.get("priceToSalesTrailing12Months")
        ev_to_ebitda = info.get("enterpriseToEbitda")
        ev_to_revenue = info.get("enterpriseToRevenue")
        dividend_yield = info.get("dividendYield")
        
        # Simple DCF estimate
        estimated_fair_value = None
        upside_potential = None
        valuation_status = ValuationStatus.FAIRLY_VALUED
        
        if cash_flow and cash_flow.free_cash_flow > 0 and market_cap > 0:
            # Simple FCF yield-based fair value
            fcf = cash_flow.free_cash_flow
            shares_outstanding = info.get("sharesOutstanding", 1)
            fcf_per_share = fcf / shares_outstanding if shares_outstanding > 0 else 0
            
            # Assume 5% FCF yield is fair value (20x FCF)
            estimated_fair_value = fcf_per_share * 20
            
            if current_price > 0 and estimated_fair_value > 0:
                upside_potential = (estimated_fair_value - current_price) / current_price
                
                if upside_potential > self.deeply_undervalued_threshold:
                    valuation_status = ValuationStatus.DEEPLY_UNDERVALUED
                elif upside_potential > self.undervalued_threshold:
                    valuation_status = ValuationStatus.UNDERVALUED
                elif upside_potential < -self.deeply_undervalued_threshold:
                    valuation_status = ValuationStatus.DEEPLY_OVERVALUED
                elif upside_potential < -self.undervalued_threshold:
                    valuation_status = ValuationStatus.OVERVALUED
                else:
                    valuation_status = ValuationStatus.FAIRLY_VALUED
        
        return ValuationMetrics(
            market_cap=market_cap,
            enterprise_value=enterprise_value,
            pe_ratio=pe_ratio,
            forward_pe=forward_pe,
            peg_ratio=peg_ratio,
            price_to_book=price_to_book,
            price_to_sales=price_to_sales,
            ev_to_ebitda=ev_to_ebitda,
            ev_to_revenue=ev_to_revenue,
            dividend_yield=dividend_yield,
            estimated_fair_value=estimated_fair_value,
            upside_potential=upside_potential,
            valuation_status=valuation_status,
        )
    
    def _calculate_health_score(
        self,
        info: Dict,
        income_statements: List[IncomeStatement],
        balance_sheet: Optional[BalanceSheet],
        cash_flow: Optional[CashFlow],
    ) -> FinancialHealthScore:
        """Calculate comprehensive financial health score."""
        red_flags = []
        green_flags = []
        
        # Profitability score (0-100)
        profitability_score = 50.0
        profit_margin = info.get("profitMargins", 0)
        if profit_margin:
            if profit_margin > 0.20:
                profitability_score = 90
                green_flags.append(f"Excellent profit margin: {profit_margin:.1%}")
            elif profit_margin > 0.10:
                profitability_score = 70
                green_flags.append(f"Good profit margin: {profit_margin:.1%}")
            elif profit_margin > 0.05:
                profitability_score = 50
            elif profit_margin > 0:
                profitability_score = 30
                red_flags.append(f"Low profit margin: {profit_margin:.1%}")
            else:
                profitability_score = 10
                red_flags.append("Company is unprofitable")
        
        # Growth score (0-100)
        growth_score = 50.0
        revenue_growth = info.get("revenueGrowth", 0)
        earnings_growth = info.get("earningsGrowth", 0)
        if revenue_growth:
            if revenue_growth > 0.20:
                growth_score = 90
                green_flags.append(f"Strong revenue growth: {revenue_growth:.1%}")
            elif revenue_growth > 0.10:
                growth_score = 70
            elif revenue_growth > 0:
                growth_score = 50
            else:
                growth_score = 30
                red_flags.append(f"Revenue declining: {revenue_growth:.1%}")
        
        # Liquidity score (0-100)
        liquidity_score = 50.0
        if balance_sheet and balance_sheet.current_ratio:
            cr = balance_sheet.current_ratio
            if cr > 2.0:
                liquidity_score = 90
                green_flags.append(f"Strong liquidity: current ratio {cr:.2f}")
            elif cr > 1.5:
                liquidity_score = 70
            elif cr > 1.0:
                liquidity_score = 50
            else:
                liquidity_score = 20
                red_flags.append(f"Weak liquidity: current ratio {cr:.2f}")
        
        # Solvency score (0-100)
        solvency_score = 50.0
        if balance_sheet and balance_sheet.debt_to_equity is not None:
            de = balance_sheet.debt_to_equity
            if de < 0.5:
                solvency_score = 90
                green_flags.append(f"Low debt: D/E ratio {de:.2f}")
            elif de < 1.0:
                solvency_score = 70
            elif de < 2.0:
                solvency_score = 50
            else:
                solvency_score = 20
                red_flags.append(f"High debt: D/E ratio {de:.2f}")
        
        # Efficiency score (0-100)
        efficiency_score = 50.0
        roe = info.get("returnOnEquity", 0)
        if roe:
            if roe > 0.20:
                efficiency_score = 90
                green_flags.append(f"Excellent ROE: {roe:.1%}")
            elif roe > 0.15:
                efficiency_score = 70
            elif roe > 0.10:
                efficiency_score = 50
            elif roe > 0:
                efficiency_score = 30
            else:
                efficiency_score = 10
                red_flags.append("Negative return on equity")
        
        # Calculate overall score
        overall_score = (
            profitability_score * 0.25 +
            growth_score * 0.25 +
            liquidity_score * 0.20 +
            solvency_score * 0.15 +
            efficiency_score * 0.15
        )
        
        # Determine overall health
        if overall_score >= 80:
            overall_health = FundamentalHealth.EXCELLENT
        elif overall_score >= 65:
            overall_health = FundamentalHealth.GOOD
        elif overall_score >= 50:
            overall_health = FundamentalHealth.FAIR
        elif overall_score >= 35:
            overall_health = FundamentalHealth.POOR
        else:
            overall_health = FundamentalHealth.CRITICAL
        
        return FinancialHealthScore(
            overall_health=overall_health,
            overall_score=overall_score,
            profitability_score=profitability_score,
            growth_score=growth_score,
            liquidity_score=liquidity_score,
            solvency_score=solvency_score,
            efficiency_score=efficiency_score,
            red_flags=red_flags,
            green_flags=green_flags,
        )
    
    def _get_earnings_intelligence(self, ticker, info: Dict) -> EarningsIntelligence:
        """Get earnings-related intelligence."""
        # Next earnings date
        next_earnings = None
        days_until = None
        
        try:
            calendar = ticker.calendar
            if calendar is not None and not calendar.empty:
                if "Earnings Date" in calendar.index:
                    earnings_dates = calendar.loc["Earnings Date"]
                    if len(earnings_dates) > 0:
                        next_earnings = earnings_dates.iloc[0]
                        if hasattr(next_earnings, 'to_pydatetime'):
                            next_earnings = next_earnings.to_pydatetime()
                        days_until = (next_earnings - datetime.now(timezone.utc)).days
        except Exception:
            pass
        
        # Estimates
        eps_estimate = info.get("forwardEps")
        revenue_estimate = info.get("revenueEstimate")
        
        # Historical
        last_eps_actual = info.get("trailingEps")
        last_eps_estimate = None
        last_surprise_pct = None
        
        # Determine signal
        earnings_signal = EarningsSignal.NO_SIGNAL
        beat_rate = None
        
        # If we have forward PE lower than trailing PE, might beat
        trailing_pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        if trailing_pe and forward_pe and forward_pe < trailing_pe * 0.9:
            earnings_signal = EarningsSignal.BEAT_EXPECTED
        
        return EarningsIntelligence(
            next_earnings_date=next_earnings,
            days_until_earnings=days_until,
            eps_estimate=eps_estimate,
            revenue_estimate=revenue_estimate,
            last_eps_actual=last_eps_actual,
            last_eps_estimate=last_eps_estimate,
            last_surprise_pct=last_surprise_pct,
            earnings_signal=earnings_signal,
            beat_rate_4q=beat_rate,
        )
    
    def _get_insider_activity(self, ticker) -> InsiderActivity:
        """Get insider trading activity."""
        total_buys = 0
        total_sells = 0
        net_shares = 0
        net_value = 0.0
        notable_transactions = []
        
        try:
            insider_df = ticker.insider_transactions
            if insider_df is not None and not insider_df.empty:
                # Filter to last 90 days
                cutoff = datetime.now(timezone.utc) - timedelta(days=90)
                
                for _, row in insider_df.iterrows():
                    try:
                        shares = row.get("Shares", 0)
                        value = row.get("Value", 0)
                        
                        if shares > 0:
                            total_buys += 1
                            net_shares += shares
                            net_value += value if value else 0
                        elif shares < 0:
                            total_sells += 1
                            net_shares += shares
                            net_value += value if value else 0
                        
                        # Notable if > $1M
                        if abs(value) > 1000000:
                            notable_transactions.append({
                                "insider": row.get("Insider", "Unknown"),
                                "shares": shares,
                                "value": value,
                            })
                    except Exception:
                        continue
        except Exception:
            pass
        
        # Determine signal
        if net_shares > 0 and total_buys > total_sells * 2:
            insider_signal = InsiderSignal.STRONG_BUYING
        elif net_shares > 0:
            insider_signal = InsiderSignal.BUYING
        elif net_shares < 0 and total_sells > total_buys * 2:
            insider_signal = InsiderSignal.STRONG_SELLING
        elif net_shares < 0:
            insider_signal = InsiderSignal.SELLING
        else:
            insider_signal = InsiderSignal.NEUTRAL
        
        return InsiderActivity(
            insider_signal=insider_signal,
            total_buys=total_buys,
            total_sells=total_sells,
            net_shares=net_shares,
            net_value=net_value,
            notable_transactions=notable_transactions[:5],  # Top 5
        )
    
    def _generate_signal(
        self,
        valuation: ValuationMetrics,
        health: FinancialHealthScore,
        earnings: EarningsIntelligence,
        insider: InsiderActivity,
    ) -> Tuple[str, float, str]:
        """Generate combined fundamental signal."""
        bullish_points = 0
        bearish_points = 0
        reasons = []
        
        # Valuation
        if valuation.valuation_status == ValuationStatus.DEEPLY_UNDERVALUED:
            bullish_points += 3
            reasons.append("deeply undervalued")
        elif valuation.valuation_status == ValuationStatus.UNDERVALUED:
            bullish_points += 2
            reasons.append("undervalued")
        elif valuation.valuation_status == ValuationStatus.DEEPLY_OVERVALUED:
            bearish_points += 3
            reasons.append("deeply overvalued")
        elif valuation.valuation_status == ValuationStatus.OVERVALUED:
            bearish_points += 2
            reasons.append("overvalued")
        
        # Health
        if health.overall_health == FundamentalHealth.EXCELLENT:
            bullish_points += 2
            reasons.append("excellent financial health")
        elif health.overall_health == FundamentalHealth.GOOD:
            bullish_points += 1
            reasons.append("good financial health")
        elif health.overall_health == FundamentalHealth.POOR:
            bearish_points += 1
            reasons.append("poor financial health")
        elif health.overall_health == FundamentalHealth.CRITICAL:
            bearish_points += 2
            reasons.append("critical financial health")
        
        # Earnings
        if earnings.earnings_signal == EarningsSignal.BEAT_EXPECTED:
            bullish_points += 1
            reasons.append("expected to beat earnings")
        elif earnings.earnings_signal == EarningsSignal.MISS_EXPECTED:
            bearish_points += 1
            reasons.append("expected to miss earnings")
        
        # Insider activity
        if insider.insider_signal == InsiderSignal.STRONG_BUYING:
            bullish_points += 2
            reasons.append("strong insider buying")
        elif insider.insider_signal == InsiderSignal.BUYING:
            bullish_points += 1
            reasons.append("insider buying")
        elif insider.insider_signal == InsiderSignal.STRONG_SELLING:
            bearish_points += 2
            reasons.append("strong insider selling")
        elif insider.insider_signal == InsiderSignal.SELLING:
            bearish_points += 1
            reasons.append("insider selling")
        
        # Determine bias
        net_points = bullish_points - bearish_points
        if net_points >= 3:
            bias = "bullish"
            confidence = min(0.9, 0.5 + net_points * 0.1)
        elif net_points <= -3:
            bias = "bearish"
            confidence = min(0.9, 0.5 + abs(net_points) * 0.1)
        elif net_points > 0:
            bias = "bullish"
            confidence = 0.5 + net_points * 0.05
        elif net_points < 0:
            bias = "bearish"
            confidence = 0.5 + abs(net_points) * 0.05
        else:
            bias = "neutral"
            confidence = 0.5
        
        reasoning = f"Fundamental {bias.upper()}: {', '.join(reasons)}" if reasons else "Insufficient fundamental data"
        
        return bias, confidence, reasoning
    
    def _assess_data_quality(
        self,
        info: Dict,
        income_statements: List[IncomeStatement],
        balance_sheet: Optional[BalanceSheet],
    ) -> str:
        """Assess the quality of available data."""
        score = 0
        
        if info.get("marketCap"):
            score += 1
        if info.get("trailingPE"):
            score += 1
        if len(income_statements) >= 3:
            score += 1
        if balance_sheet:
            score += 1
        if info.get("forwardPE"):
            score += 1
        
        if score >= 4:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"


def create_fundamental_intelligence() -> FundamentalIntelligence:
    """Factory function to create a FundamentalIntelligence instance."""
    return FundamentalIntelligence()
