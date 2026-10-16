"""Ingestion layer (pipeline stage 1 DATA): local fixtures, provenance.

Nothing downloads at runtime; nothing touches the network.
"""

from .openfootball import REPO_ROOT, ImportResult, import_fixture, load_records, merge_records

__all__ = [
    "REPO_ROOT",
    "ImportResult",
    "import_fixture",
    "load_records",
    "merge_records",
]
