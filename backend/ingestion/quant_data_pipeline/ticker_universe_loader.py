from pathlib import Path

import yaml

from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import ConfigurationError

_UNIVERSE_PATH = Path(__file__).parent / "config" / "ticker_universe.yaml"


def load_ticker_universe(path: Path | None = None) -> list[str]:
    """Load canonical ticker list from YAML; uppercase-normalize."""
    target = path if path is not None else _UNIVERSE_PATH
    try:
        text = target.read_text()
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Ticker universe file not found: {target}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Failed to parse ticker universe YAML at {target}") from exc
    try:
        tickers = data["tickers"]
    except (TypeError, KeyError) as exc:
        raise ConfigurationError(
            f"Ticker universe YAML at {target} is missing 'tickers' key"
        ) from exc
    return [str(t).upper() for t in tickers]
