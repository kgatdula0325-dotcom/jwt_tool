import logging
import requests

logger = logging.getLogger(__name__)

TABBY_CARD_LIMIT_URL = "https://api.tabby.ai/api/v2/customer/card/limit"
DEFAULT_TIMEOUT = 30


def modify_card_limit(
    customer_id: str,
    new_limit: float,
    bearer_token: str,
    reason: str = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Modify the card limit for a Tabby customer.

    Args:
        customer_id: The unique identifier of the customer.
        new_limit: The new card limit to set for the customer.
        bearer_token: A valid Bearer token for API authorization.
        reason: An optional reason for changing the card limit.
        timeout: Request timeout in seconds (default: 30).

    Returns:
        A dict with keys 'success' (bool), 'status_code' (int), and 'data' or 'error'.

    Raises:
        ValueError: If customer_id is empty or new_limit is negative.
    """
    if not customer_id:
        raise ValueError("customer_id must not be empty.")
    if new_limit < 0:
        raise ValueError("new_limit must be a non-negative value.")
    if not bearer_token:
        raise ValueError("bearer_token must not be empty.")

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "customer_id": customer_id,
        "limit": new_limit,
    }
    if reason is not None:
        payload["reason"] = reason

    logger.debug(
        "Sending card limit modification request: customer_id=%s, new_limit=%s, reason=%s",
        customer_id,
        new_limit,
        reason,
    )

    try:
        response = requests.post(TABBY_CARD_LIMIT_URL, json=payload, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout:
        logger.error("Request to Tabby API timed out.")
        return {"success": False, "status_code": None, "error": "Request timed out."}
    except requests.exceptions.ConnectionError as exc:
        logger.error("Connection error when calling Tabby API: %s", exc)
        return {"success": False, "status_code": None, "error": f"Connection error: {exc}"}
    except requests.exceptions.RequestException as exc:
        logger.error("Unexpected error when calling Tabby API: %s", exc)
        return {"success": False, "status_code": None, "error": f"Request error: {exc}"}

    status_code = response.status_code
    logger.debug("Tabby API response: status_code=%s, body=%s", status_code, response.text)

    try:
        response_data = response.json()
    except ValueError:
        response_data = response.text

    if status_code == 200:
        logger.info("Card limit successfully updated for customer_id=%s.", customer_id)
        return {"success": True, "status_code": status_code, "data": response_data}

    if status_code == 400:
        logger.error("Bad request (400): Invalid input. Response: %s", response_data)
        return {
            "success": False,
            "status_code": status_code,
            "error": "Bad request: The request contained invalid parameters.",
            "details": response_data,
        }

    if status_code == 401:
        logger.error("Unauthorized (401): Bearer token is missing or invalid.")
        return {
            "success": False,
            "status_code": status_code,
            "error": "Unauthorized: The Bearer token is missing or invalid.",
            "details": response_data,
        }

    if status_code == 403:
        logger.error("Forbidden (403): The token does not have permission to perform this action.")
        return {
            "success": False,
            "status_code": status_code,
            "error": "Forbidden: Insufficient permissions to modify the card limit.",
            "details": response_data,
        }

    if status_code == 422:
        logger.error("Unprocessable entity (422): Validation failed. Response: %s", response_data)
        return {
            "success": False,
            "status_code": status_code,
            "error": "Unprocessable entity: The request data failed validation.",
            "details": response_data,
        }

    logger.warning("Unexpected response status_code=%s. Response: %s", status_code, response_data)
    return {
        "success": False,
        "status_code": status_code,
        "error": f"Unexpected response with status code {status_code}.",
        "details": response_data,
    }
