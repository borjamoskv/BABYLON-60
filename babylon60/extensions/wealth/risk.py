# [C5-REAL] Exergy-Maximized
"""moneytv-1 Trading Bot Architecture v1.1 - Risk Management.

With circuit breakers and tamper-evident risk management.
Decimal-precision. Zero tolerance for float drift.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto

log = logging.getLogger(__name__)


class Signal(Enum):
    STRONG_BUY = auto()
    BUY = auto()
    NEUTRAL = auto()
    SELL = auto()
    STRONG_SELL = auto()
    EMERGENCY_EXIT = auto()  # Total liquidation


@dataclass(frozen=True)
class Position:
    """Immutable position descriptor."""

    __slots__ = (
        "correlation_id",
        "entry_price",
        "max_hold_time",
        "side",
        "size",
        "stop_loss",
        "symbol",
        "take_profit",
        "timestamp",
    )
    symbol: str
    side: str  # "long" | "short"
    entry_price: Decimal
    size: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    max_hold_time: int  # maximum hours
    timestamp: float
    correlation_id: str  # For correlation tracking


@dataclass
class Portfolio:
    """Snapshot of the portfolio state at a given instant."""

    total_equity: Decimal
    daily_pnl: Decimal
    peak_equity: Decimal
    positions: list[Position] = field(default_factory=list)

    @property
    def current_drawdown(self) -> Decimal:
        """Current drawdown relative to historical peak."""
        if self.peak_equity == 0:
            return Decimal("0")
        return (self.peak_equity - self.total_equity) / self.peak_equity

    @property
    def daily_loss_pct(self) -> Decimal:
        """Daily loss as a fraction of equity."""
        if self.total_equity == 0:
            return Decimal("0")
        return self.daily_pnl / self.total_equity


class RiskManager:
    """
    Sovereign risk management. NEVER deactivated.
    Automatic circuit breakers included.
    All thresholds in Decimal - zero float drift.
    """

    # Absolute limits (Decimal - without precision loss)
    MAX_POSITION_PCT = Decimal("0.05")  # 5% per position
    MAX_DAILY_LOSS_PCT = Decimal("0.02")  # Daily stop -2%
    MAX_DRAWDOWN_PCT = Decimal("0.10")  # Total stop -10%
    MAX_CORRELATED: int = 3  # Maximum 3 correlated positions
    MAX_LEVERAGE = Decimal("3.0")  # Maximum leverage
    COOLDOWN_SECONDS: int = 60  # Minimum 60s between trades of the same symbol

    def __init__(self) -> None:
        self.circuit_breaker_triggered = False
        self.consecutive_rejections = 0
        self.MAX_CONSECUTIVE_REJECTIONS = 3
        self._cb_timer: threading.Timer | None = None

    def approve_trade(self, position: Position, portfolio: Portfolio) -> bool:
        """Every trade MUST pass through here. No exceptions."""
        if self.circuit_breaker_triggered:
            log.warning("🚨 CIRCUIT BREAKER ACTIVE. Trading paused.")
            return False

        checks = [
            ("position_size", self._check_position_size(position, portfolio)),
            ("daily_loss", self._check_daily_loss(portfolio)),
            ("drawdown", self._check_drawdown(portfolio)),
            ("correlation", self._check_correlation(position, portfolio)),
            ("leverage", self._check_leverage(position)),
            ("cooldown", self._check_cooldown_period(position, portfolio)),
        ]

        failed = [name for name, passed in checks if not passed]

        if failed:
            self.consecutive_rejections += 1
            log.warning(
                "Trade REJECTED - failed checks: %s (consecutive: %d/%d)",
                failed,
                self.consecutive_rejections,
                self.MAX_CONSECUTIVE_REJECTIONS,
            )
            if self.consecutive_rejections >= self.MAX_CONSECUTIVE_REJECTIONS:
                self._trigger_circuit_breaker()
            return False

        self.consecutive_rejections = max(0, self.consecutive_rejections - 1)
        log.info("Trade APPROVED: %s %s (size=%s)", position.side, position.symbol, position.size)
        return True

    def _check_position_size(self, position: Position, portfolio: Portfolio) -> bool:
        """Rejects if position exceeds MAX_POSITION_PCT of total equity."""
        if portfolio.total_equity <= 0:
            log.warning("Equity ≤ 0, rejecting trade.")
            return False
        ratio = position.size / portfolio.total_equity
        if ratio > self.MAX_POSITION_PCT:
            log.warning(
                "Position size %.2f%% > max %.2f%%",
                ratio * 100,
                self.MAX_POSITION_PCT * 100,
            )
            return False
        return True

    def _check_daily_loss(self, portfolio: Portfolio) -> bool:
        """Rejects if daily loss exceeds MAX_DAILY_LOSS_PCT."""
        if portfolio.total_equity <= 0:
            return False
        loss_pct = portfolio.daily_loss_pct
        if loss_pct < -self.MAX_DAILY_LOSS_PCT:
            log.warning(
                "Daily loss %.2f%% > max -%.2f%%",
                loss_pct * 100,
                self.MAX_DAILY_LOSS_PCT * 100,
            )
            return False
        return True

    def _check_drawdown(self, portfolio: Portfolio) -> bool:
        """Rejects if accumulated drawdown exceeds MAX_DRAWDOWN_PCT."""
        dd = portfolio.current_drawdown
        if dd > self.MAX_DRAWDOWN_PCT:
            log.warning(
                "Drawdown %.2f%% > max %.2f%%",
                dd * 100,
                self.MAX_DRAWDOWN_PCT * 100,
            )
            return False
        return True

    def _check_correlation(self, position: Position, portfolio: Portfolio) -> bool:
        """Rejects if there are already MAX_CORRELATED positions of the same symbol."""
        same_symbol = sum(1 for p in portfolio.positions if p.symbol == position.symbol)
        if same_symbol >= self.MAX_CORRELATED:
            log.warning(
                "Correlation: %d positions of %s (max %d)",
                same_symbol,
                position.symbol,
                self.MAX_CORRELATED,
            )
            return False
        return True

    def _check_leverage(self, position: Position) -> bool:
        """Rejects if implicit leverage exceeds MAX_LEVERAGE."""
        if position.size <= 0 or position.entry_price <= 0:
            return False
        # Leverage = notional / margin (size is margin, entry_price * size = notional)
        # Simplified: if position explicitly carries leverage info, check it.
        # For now, we check if size * entry_price / size > MAX_LEVERAGE conceptually.
        # The real check: position.size is the margin; notional = entry_price * contracts.
        # We approximate: if the stop distance is tighter than 1/MAX_LEVERAGE, leverage is too high.
        risk_per_unit = abs(position.entry_price - position.stop_loss)
        if risk_per_unit == 0:
            log.warning("Stop loss = entry price, infinite leverage.")
            return False
        effective_leverage = position.entry_price / risk_per_unit
        if effective_leverage > self.MAX_LEVERAGE:
            log.warning(
                "Leverage efectivo %.1fx > max %.1fx",
                effective_leverage,
                self.MAX_LEVERAGE,
            )
            return False
        return True

    def _check_cooldown_period(
        self,
        position: Position,
        portfolio: Portfolio,
    ) -> bool:
        """Rejects if a position of the same symbol was opened < COOLDOWN_SECONDS ago."""
        now = time.monotonic()
        for p in portfolio.positions:
            if p.symbol == position.symbol:
                elapsed = now - p.timestamp
                if elapsed < self.COOLDOWN_SECONDS:
                    log.warning(
                        "Cooldown: %s opened %.0fs ago (min %ds)",
                        position.symbol,
                        elapsed,
                        self.COOLDOWN_SECONDS,
                    )
                    return False
        return True

    def _trigger_circuit_breaker(self, reset_seconds: int = 86400) -> None:
        """Pauses trading for reset_seconds after N consecutive rejections."""
        self.circuit_breaker_triggered = True
        log.critical(
            "🚨 CIRCUIT BREAKER ACTIVATED. %dh pause.",
            reset_seconds // 3600,
        )
        # Auto-reset via background thread
        if self._cb_timer is not None:
            self._cb_timer.cancel()
        self._cb_timer = threading.Timer(
            reset_seconds,
            self._reset_circuit_breaker,
        )
        self._cb_timer.daemon = True
        self._cb_timer.start()

    def _reset_circuit_breaker(self) -> None:
        self.circuit_breaker_triggered = False
        self.consecutive_rejections = 0
        log.info("✅ Circuit breaker reset.")
