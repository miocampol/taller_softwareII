"""Response checks shared by Locust and unit tests (no HTTP side effects)."""

from datetime import date
from uuid import uuid4


def bulk_payload():
    token = uuid4().hex
    return {"users": [
        {"name": f"Locust {token[:8]} {index}",
         "email": f"locust.{token}.{index}@example.com",
         "birth_date": "1990-01-01"}
        for index in range(3)
    ]}


def validate_page(body, endpoint, page, per_page):
    if not isinstance(body, dict) or not isinstance(body.get("data"), list):
        return "Expected a paginated JSON object with data"
    if type(body.get("total")) is not int or body["total"] < 0:
        return "Invalid total"
    if body.get("current_page") != page or body.get("per_page") != per_page:
        return "Pagination does not match the request"
    if len(body["data"]) > per_page:
        return "Page exceeds requested size"
    if len(body["data"]) != min(per_page, max(0, body["total"] - (page - 1) * per_page)):
        return "Page length does not match total"
    cutoff = None
    if endpoint.endswith("over-twenty"):
        try:
            cutoff = date.fromisoformat(body["cutoff_date"])
        except (KeyError, TypeError, ValueError):
            return "Invalid cutoff_date"
    ids = []
    for row in body["data"]:
        if not isinstance(row, dict) or type(row.get("id")) is not int or not isinstance(row.get("email"), str):
            return "Invalid user fields"
        if "password" in row or "remember_token" in row:
            return "Sensitive fields exposed"
        if endpoint.endswith("emails") and set(row) != {"id", "email"}:
            return "Email endpoint returned unexpected fields"
        if cutoff:
            try:
                birth_date = date.fromisoformat(row["birth_date"][:10])
            except (KeyError, TypeError, ValueError):
                return "Invalid birth_date"
            if birth_date >= cutoff:
                return "Age filter included a user not older than twenty"
        ids.append(row["id"])
    if ids != sorted(set(ids)):
        return "Users are not ordered by unique id"
    return None


def validate_bulk(body, payload):
    if not isinstance(body, dict) or not isinstance(body.get("users"), list) or len(body["users"]) != 3:
        return "Expected three created users"
    expected = {row["email"] for row in payload["users"]}
    actual = []
    ids = []
    for row in body["users"]:
        if not isinstance(row, dict) or type(row.get("id")) is not int or not isinstance(row.get("email"), str):
            return "Invalid created user"
        if "password" in row or "remember_token" in row:
            return "Sensitive fields exposed"
        actual.append(row.get("email"))
        ids.append(row["id"])
    if len(set(ids)) != 3 or set(actual) != expected:
        return "Created users do not match the submitted batch"
    return None
