import json
import re


MASK = "[REDACTED]"

SENSITIVE_KEYS = {
    "apikey",
    "anthropicapikey",
    "password",
    "passwd",
    "secret",
    "clientsecret",
    "token",
    "accesstoken",
    "refreshtoken",
    "authorization",
    "cookie",
    "setcookie",
}

EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
BEARER = re.compile(
    r"\bBearer\s+[A-Za-z0-9._~+/=-]+",
    re.IGNORECASE,
)


class Redactor:
    def __init__(self, secrets=()):
        self.secrets = sorted(
            {
                value
                for value in secrets
                if isinstance(value, str) and value
            },
            key=len,
            reverse=True,
        )

    def text(self, value: str) -> str:
        for secret in self.secrets:
            value = value.replace(secret, MASK)

        value = BEARER.sub("Bearer " + MASK, value)
        return EMAIL.sub(MASK, value)

    def clean(self, value):
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                normalized = re.sub(
                    r"[^a-z0-9]", "", str(key).lower()
                )
                result[self.text(str(key))] = (
                    MASK
                    if normalized in SENSITIVE_KEYS
                    else self.clean(item)
                )
            return result

        if isinstance(value, (list, tuple)):
            return [self.clean(item) for item in value]

        if isinstance(value, str):
            # Tool results may contain JSON serialized inside a string.
            try:
                decoded = json.loads(value)
            except (json.JSONDecodeError, RecursionError):
                return self.text(value)

            if isinstance(decoded, (dict, list)):
                return json.dumps(
                    self.clean(decoded),
                    ensure_ascii=False,
                )

            return self.text(value)

        return value