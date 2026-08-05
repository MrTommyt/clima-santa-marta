from __future__ import annotations

from clima_shared.runtime import load_source_config, run_cli

from ingestion_openmeteo.adapter import OpenMeteoHistoricalAdapter


def main() -> None:
    adapter = OpenMeteoHistoricalAdapter(load_source_config("openmeteo_historical"))
    run_cli(adapter)


if __name__ == "__main__":
    main()
