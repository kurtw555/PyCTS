import time
from typing import Optional

import requests

from .models import ApiProblem


class NWSApiError(Exception):
    """Error returned by the NOAA weather API."""

    def __init__(self, message: str, status_code: int = 0, problem: Optional[ApiProblem] = None):
        super().__init__(message)
        self.status_code = status_code
        self.problem = problem


class HttpTransport:
    def __init__(self, user_agent: str, timeout: float = 10.0, retries: int = 2):
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "application/geo+json",
            }
        )

    def get_json(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> dict:
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response.status_code >= 400:
                    raise self._build_error(response)
                return response.json()
            except (requests.RequestException, ValueError, NWSApiError) as exc:
                last_error = exc
                if isinstance(exc, NWSApiError) and exc.status_code < 500 and exc.status_code != 429:
                    break
                if attempt < self.retries:
                    time.sleep(0.8 * (attempt + 1))

        if isinstance(last_error, NWSApiError):
            raise last_error
        raise NWSApiError(f"Request failed: {last_error}")

    def _build_error(self, response: requests.Response) -> NWSApiError:
        problem = None
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if isinstance(payload, dict):
            problem = ApiProblem(
                type=str(payload.get("type", "")),
                title=str(payload.get("title", "Request Failed")),
                status=int(payload.get("status", response.status_code)),
                detail=str(payload.get("detail", response.text[:200])),
                instance=str(payload.get("instance", "")),
                correlation_id=str(payload.get("correlationId", "")),
            )

        if problem:
            message = f"{problem.title}: {problem.detail}"
        else:
            message = f"HTTP {response.status_code}: {response.text[:200]}"
        return NWSApiError(message, status_code=response.status_code, problem=problem)
