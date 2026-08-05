from __future__ import annotations

from clima_shared.runtime import load_source_config, run_cli

from ingestion_metar.adapter import MetarObservationsAdapter


def main() -> None:
    adapter = MetarObservationsAdapter(load_source_config("metar_observations"))
    run_cli(adapter)


if __name__ == "__main__":
    main()
