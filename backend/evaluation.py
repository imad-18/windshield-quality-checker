"""
Evaluation service — determines if windshield passes quality control.

Checks whether the final stabilised intensity falls within [min, max].
Stabilisation = last N readings have std deviation below a threshold.
"""

import logging
import statistics
from dataclasses import dataclass

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    passed: bool
    final_intensity: float
    final_resistance: float
    readings_count: int
    is_stable: bool


class EvaluationService:
    """Evaluates conformity of a windshield based on intensity readings."""

    def __init__(
        self,
        window: int = settings.stabilization_window,
        threshold: float = settings.stabilization_threshold,
    ):
        self.window = window
        self.threshold = threshold

    def is_stable(self, readings: list[float]) -> bool:
        """Check if the latest readings have converged (low std dev)."""
        if len(readings) < self.window:
            return False

        last_n = readings[-self.window:]
        std = statistics.stdev(last_n)
        return std <= self.threshold

    def evaluate(
        self,
        readings: list[float],
        tension: float,
        min_intensity: float,
        max_intensity: float,
    ) -> EvaluationResult:
        """
        Evaluate the test result.
        Uses the mean of the last `window` readings as the final intensity.
        """
        if not readings:
            return EvaluationResult(
                passed=False,
                final_intensity=0.0,
                final_resistance=0.0,
                readings_count=0,
                is_stable=False,
            )

        stable = self.is_stable(readings)
        last_n = readings[-self.window:] if len(readings) >= self.window else readings
        final_intensity = round(statistics.mean(last_n), 3)
        final_resistance = round(tension / final_intensity, 2) if final_intensity > 0 else 0.0

        passed = min_intensity <= final_intensity <= max_intensity

        logger.info(
            f"Evaluation: I={final_intensity}A  R={final_resistance}Ω  "
            f"range=[{min_intensity}, {max_intensity}]  "
            f"stable={stable}  passed={passed}"
        )

        return EvaluationResult(
            passed=passed,
            final_intensity=final_intensity,
            final_resistance=final_resistance,
            readings_count=len(readings),
            is_stable=stable,
        )


# Singleton instance
evaluation_service = EvaluationService()
