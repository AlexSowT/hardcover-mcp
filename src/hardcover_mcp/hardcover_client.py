import httpx
import re
from typing import Any, Dict, List, Mapping, Union

from fastmcp import Context
from fastmcp.exceptions import ToolError


_VARIABLE_PATTERN = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


def _normalize_variable_name(name: Any) -> str:
    if not isinstance(name, str):
        name = str(name)
    normalized = name.lstrip("$").strip()
    if not normalized:
        raise ToolError("Variable names must be non-empty strings")
    return normalized


def _normalize_variables(
    variables: Union[Mapping[str, Any], List[Any], None],
) -> Dict[str, Any]:
    if variables is None:
        return {}

    if isinstance(variables, Mapping):
        return {
            _normalize_variable_name(key): value for key, value in variables.items()
        }

    if isinstance(variables, list):
        normalized: Dict[str, Any] = {}
        for entry in variables:
            if isinstance(entry, Mapping):
                if len(entry) != 1:
                    raise ToolError(
                        "Variable mappings must contain exactly one key/value pair"
                    )
                key, value = next(iter(entry.items()))
            elif isinstance(entry, (list, tuple)) and len(entry) == 2:
                key, value = entry
            else:
                raise ToolError(
                    "Variable lists must contain either 2-item sequences or single-entry mappings"
                )

            normalized[_normalize_variable_name(key)] = value

        return normalized

    raise ToolError("Variables must be provided as a dict or a list of key/value pairs")


def _extract_query_variables(query: str) -> set[str]:
    if not query:
        return set()
    return set(_VARIABLE_PATTERN.findall(query))


class HardcoverClient:
    _GRAPHQL_URL = "https://api.hardcover.app/v1/graphql"

    def __init__(self, auth_header: str) -> None:
        if not auth_header or not isinstance(auth_header, str):
            raise ValueError("auth_header must be a non-empty string")
        self.auth_header = auth_header

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
        }

    async def query(
        self,
        query: str,
        ctx: Context,
        variables: Union[Mapping[str, Any], List[Any], None] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        normalized_variables = _normalize_variables(variables)
        required_variables = _extract_query_variables(query)

        if required_variables:
            missing = sorted(
                var for var in required_variables if var not in normalized_variables
            )
            if missing:
                raise ToolError(
                    "Missing variables for GraphQL query: " + ", ".join(missing)
                )

        payload = {"query": query}

        if normalized_variables:
            if required_variables:
                payload["variables"] = {
                    key: normalized_variables[key] for key in required_variables
                }
            else:
                payload["variables"] = normalized_variables

        async with httpx.AsyncClient(timeout=timeout, headers=self.headers) as client:
            resp = await client.post(self._GRAPHQL_URL, json=payload)
            resp.raise_for_status()
            result = resp.json()

        if "errors" in result:
            raise RuntimeError(result["errors"])

        return result.get("data", result)
