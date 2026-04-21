import os


def get_env(name: str, default: str | None = None) -> str | None:
    # Support direct names plus common CI secret aliases.
    for key in (name, f"GITHUB_{name}", f"SECRET_{name}", f"GH_{name}"):
        value = os.getenv(key)
        if value is not None and value != "":
            return value
    return default
