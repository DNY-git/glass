"""Forecast distributions (pipeline stage 6): frozen analytic snapshots.

The pure, deterministic forecast builder and record: a forecast is a
fitted Poisson model projected through the scoreline matrix at a
fixture-date cutoff enforced inside the builder, with the analytic
outcome probabilities stored at full precision. Frozen at creation,
self-verifying via a content hash under the written canonicalization
spec, and honest about its flags — in-sample point estimates pending
chronological evaluation (Phases 9/11), never evidence of accuracy.
No storage, no HTTP, no filesystem, no randomness, no wall clock.
"""

from .builder import build_forecast
from .canonicalization import (
    canonical_payload,
    config_identity,
    content_hash,
    fitted_from_payload,
    fitted_payload,
)
from .constants import FORECAST_VERSION
from .record import Forecast, ForecastConflictError, ForecastIntegrityError

__all__ = [
    "FORECAST_VERSION",
    "Forecast",
    "ForecastConflictError",
    "ForecastIntegrityError",
    "build_forecast",
    "canonical_payload",
    "config_identity",
    "content_hash",
    "fitted_from_payload",
    "fitted_payload",
]
