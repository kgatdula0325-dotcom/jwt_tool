from __future__ import annotations

import logging
import math
from typing import Any, Optional, Union

import requests

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

TABBY_CARD_LIMIT_URL = "https://api.tabby.ai/api/v2/customer/card/limit"
DEFAULT_TIMEOUT = 30


class ModifyCardLimitResult(TypedDict, total=False):
    success: bool
    status_code: Optional[int]
    data: Any
    error: str
    details: Any


def _error_result(
    message: str,
    status_code: Optional[int] = None,
    details: Any = None,
) -> ModifyCardLimitResult:
    result: ModifyCardLimitResult = {
        "success": False,
        "status_code": status_code,
        "error": message,
    }
    if details is not None:
        result["details"] = details
    return result


def modify_card_limit(
    customer_id: str,
    new_limit: float,
    bearer_token: str,
    reason: Optional[str] = None,
    timeout: Union[int, float] = DEFAULT_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> ModifyCardLimitResult:
    """Modify the card limit for a Tabby customer.

    Args:
        customer_id: The unique identifier of the customer.
        new_limit: The new card limit to set for the customer (non-negative finite number).
        bearer_token: A valid Bearer token for API authorization.
        reason: Optional reason for changing the card limit.
        timeout: Request timeout in seconds (must be greater than 0).
        session: Optional requests session for connection reuse and testing.

    Returns:
        A ModifyCardLimitResult with:
          - success: Whether the request succeeded.
          - status_code: HTTP status code if available.
          - data: Parsed response body on success.
          - error: Error message on failure.
          - details: Parsed response body on failure, if available.

    Raises:
        ValueError: If inputs are invalid.
    """
    if not customer_id or not customer_id.strip():
        raise ValueError("customer_id must not be empty.")
    if not isinstance(new_limit, (int, float)):
        raise ValueError("new_limit must be a number.")
    if math.isnan(new_limit) or math.isinf(new_limit) or new_limit < 0:
        raise ValueError("new_limit must be a finite non-negative number.")
    if not bearer_token or not bearer_token.strip():
        raise ValueError("bearer_token must not be empty.")
    if timeout <= 0:
        raise ValueError("timeout must be greater than 0.")

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    payload: dict = {
        "customer_id": customer_id.strip(),
        "limit": new_limit,
    }
    if reason is not None:
        payload["reason"] = reason

    logger.debug(
        "Sending card limit modification request: customer_id=%s, new_limit=%s, reason_provided=%s",
        customer_id,
        new_limit,
        reason is not None,
    )

    client = session if session is not None else requests

    try:
        response = client.post(
            TABBY_CARD_LIMIT_URL,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        logger.error("Request to Tabby API timed out.")
        return _error_result("Request timed out.")
    except requests.exceptions.ConnectionError as exc:
        logger.error("Connection error when calling Tabby API: %s", exc)
        return _error_result(f"Connection error: {exc}")
    except requests.exceptions.RequestException as exc:
        logger.error("Unexpected error when calling Tabby API: %s", exc)
        return _error_result(f"Request error: {exc}")

    status_code = response.status_code
    logger.debug("Tabby API response received: status_code=%s", status_code)

    try:
        response_data = response.json()
    except ValueError:
        response_data = response.text

    if 200 <= status_code < 300:
        logger.info("Card limit successfully updated for customer_id=%s.", customer_id)
        return {
            "success": True,
            "status_code": status_code,
            "data": response_data,
        }

    error_map = {
        400: "Bad request: The request contained invalid parameters.",
        401: "Unauthorized: The Bearer token is missing or invalid.",
        403: "Forbidden: Insufficient permissions to modify the card limit.",
        422: "Unprocessable entity: The request data failed validation.",
    }

    message = error_map.get(status_code, f"Unexpected response with status code {status_code}.")
    logger.warning("Tabby API request failed: status_code=%s", status_code)

    return _error_result(message, status_code=status_code, details=response_data)
