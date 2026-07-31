"""BlackRock Aladdin REST client — the internal side of the reconciliation.

Aladdin is Northwind's system of record: what the firm believes it holds and
what it believes it traded. It is the easy side of this problem — structured,
API-accessible, already in the pipeline. The hard side is the counterparty PDFs
the rest of this package deals with. Reconciliation proves the two agree.

Three things this module is careful about.

**Paging is not optional.** A single EM portfolio can return tens of thousands
of positions. The client yields pages lazily so a full pull never materialises
the whole book in memory, and so a partial failure loses one page rather than an
afternoon.

**Values come back as ``Decimal``.** Aladdin sends JSON numbers; ``json.loads``
turns those into floats, and a float quantity compared against a Decimal
quantity with a 0.0001 tolerance produces breaks that are not breaks. Parsing
with ``parse_float=Decimal`` fixes it at the boundary rather than everywhere
downstream.

**The output schema matches the counterparty side exactly.** Both feeds land on
``account_number`` / ``security_id`` / ``quantity`` / ``market_value`` /
``currency`` so ``recon/reconcile.py`` can full-outer-join them without either
side having a privileged shape.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Iterator

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from core.clients import secret

log = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 500
DEFAULT_TIMEOUT_SECONDS = 60.0

# Columns the reconciliation engine expects from the internal side.
POSITION_COLUMNS: tuple[str, ...] = (
    "account_number",
    "security_id",
    "security_name",
    "quantity",
    "market_value",
    "currency",
    "as_of_date",
)

TRADE_COLUMNS: tuple[str, ...] = (
    "account_number",
    "security_id",
    "trade_id",
    "side",
    "quantity",
    "price",
    "currency",
    "trade_date",
    "settlement_date",
)


class AladdinError(RuntimeError):
    """A non-retryable response from Aladdin."""


def _is_retryable(exc: BaseException) -> bool:
    """Transport failures and Aladdin's own throttling are worth another try.

    Imported inside the function for the same reason as in ``core/clients.py``:
    keeping heavy third-party imports off module import paths that pure modules
    depend on.
    """
    import httpx

    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return False


@dataclass(frozen=True)
class AladdinConfig:
    """Connection settings. The API key is never a literal in configuration."""

    base_url: str
    api_key: str
    page_size: int = DEFAULT_PAGE_SIZE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


class AladdinClient:
    """Paged reader over the Aladdin positions and trades endpoints."""

    def __init__(self, config: AladdinConfig) -> None:
        self.config = config

    @classmethod
    def from_environment(cls) -> "AladdinClient":
        """Build a client, reading the API key from Key Vault via managed identity.

        Aladdin is one of the two credentials in this system that cannot be an
        Azure RBAC role, so it lives in Key Vault and is read with the Function's
        own identity — never written into application settings.
        """
        return cls(
            AladdinConfig(
                base_url=os.environ["ALADDIN_BASE_URL"].rstrip("/"),
                api_key=secret(
                    os.environ["KEY_VAULT_URL"],
                    os.environ.get("ALADDIN_SECRET_NAME", "aladdin-api-key"),
                ),
                page_size=int(os.environ.get("ALADDIN_PAGE_SIZE", DEFAULT_PAGE_SIZE)),
            )
        )

    # -- transport ----------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "VND.com.blackrock.API-Key": self.config.api_key,
            "Accept": "application/json",
        }

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """One GET, with backoff on throttling and transport errors."""
        import httpx

        url = f"{self.config.base_url}{path}"
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.get(url, params=params, headers=self._headers())
            response.raise_for_status()
            # parse_float=Decimal: never let a position quantity become a float.
            return json.loads(response.text, parse_float=Decimal)

    def _iter_pages(self, path: str, params: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """Walk a cursor-paged endpoint, yielding each record.

        Aladdin returns ``{"data": [...], "nextPageToken": "..."}``. The token is
        absent or empty on the final page.
        """
        page_params = {**params, "pageSize": self.config.page_size}
        page_number = 0

        while True:
            payload = self._get(path, page_params)
            records = payload.get("data") or []
            page_number += 1

            log.info(
                "aladdin_page_fetched",
                extra={"path": path, "page": page_number, "records": len(records)},
            )
            yield from records

            token = payload.get("nextPageToken")
            if not token:
                return
            page_params = {**page_params, "pageToken": token}

    # -- endpoints ----------------------------------------------------------

    def iter_positions(
        self, as_of: date, portfolio_ids: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        """Yield canonical position records as of a date."""
        params: dict[str, Any] = {"asOfDate": as_of.isoformat()}
        if portfolio_ids:
            params["portfolios"] = ",".join(portfolio_ids)

        for record in self._iter_pages("/api/positions", params):
            yield _position_record(record, as_of)

    def iter_trades(self, from_date: date, to_date: date) -> Iterator[dict[str, Any]]:
        """Yield canonical trade records over a date range."""
        params = {"fromDate": from_date.isoformat(), "toDate": to_date.isoformat()}
        for record in self._iter_pages("/api/trades", params):
            yield _trade_record(record)

    # -- frames -------------------------------------------------------------

    def positions_frame(self, as_of: date, portfolio_ids: list[str] | None = None):
        """Positions as a DataFrame shaped for :mod:`recon.reconcile`."""
        import pandas as pd

        rows = list(self.iter_positions(as_of, portfolio_ids))
        return pd.DataFrame(rows, columns=list(POSITION_COLUMNS), dtype=object)

    def trades_frame(self, from_date: date, to_date: date):
        """Trades as a DataFrame, used to match counterparty confirmations."""
        import pandas as pd

        rows = list(self.iter_trades(from_date, to_date))
        return pd.DataFrame(rows, columns=list(TRADE_COLUMNS), dtype=object)


# -----------------------------------------------------------------------------
# Record mapping — Aladdin's names to Northwind's canonical names
# -----------------------------------------------------------------------------


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _position_record(record: dict[str, Any], as_of: date) -> dict[str, Any]:
    """One Aladdin position in canonical form.

    The mapping lives here rather than in the reconciliation so that a field
    rename on the Aladdin side is one edit in one file.
    """
    return {
        "account_number": str(record.get("portfolioId") or "").strip(),
        "security_id": str(record.get("securityId") or "").strip(),
        "security_name": (record.get("securityDescription") or None),
        "quantity": _decimal(record.get("quantity")),
        "market_value": _decimal(record.get("marketValue")),
        "currency": (record.get("currency") or "").upper() or None,
        "as_of_date": as_of,
    }


def _trade_record(record: dict[str, Any]) -> dict[str, Any]:
    """One Aladdin trade in canonical form."""
    return {
        "account_number": str(record.get("portfolioId") or "").strip(),
        "security_id": str(record.get("securityId") or "").strip(),
        "trade_id": str(record.get("tradeId") or "").strip(),
        "side": (record.get("side") or "").upper() or None,
        "quantity": _decimal(record.get("quantity")),
        "price": _decimal(record.get("price")),
        "currency": (record.get("currency") or "").upper() or None,
        "trade_date": record.get("tradeDate"),
        "settlement_date": record.get("settlementDate"),
    }
