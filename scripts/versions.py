"""Look up test versions: phcc releases and the aiounifi pin of Home Assistant.

  versions.py                  Home Assistant pin of the newest phcc releases
  versions.py --ha 2026.11.1   aiounifi pin and matching phcc release of a version

pytest-homeassistant-custom-component (phcc) pins one Home Assistant version per
release in its PyPI metadata, the UniFi integration pins aiounifi in its manifest.
"""

import argparse
import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

PHCC_URL = "https://pypi.org/pypi/pytest-homeassistant-custom-component/json"
PHCC_VERSION_URL = (
    "https://pypi.org/pypi/pytest-homeassistant-custom-component/{version}/json"
)
UNIFI_MANIFEST_URL = (
    "https://raw.githubusercontent.com/home-assistant/core/{ha}"
    "/homeassistant/components/unifi/manifest.json"
)


def get_json(url: str) -> dict:
    """Fetch a JSON document."""
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def version_key(version: str) -> tuple[int, ...]:
    """Sort key for plain numeric versions, others sort first."""
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return ()


def phcc_releases(count: int) -> list[tuple[str, str | None]]:
    """Return the newest phcc releases with their Home Assistant pin."""
    versions = sorted(get_json(PHCC_URL)["releases"], key=version_key, reverse=True)
    releases = []
    for version in versions[:count]:
        requires = get_json(PHCC_VERSION_URL.format(version=version))["info"][
            "requires_dist"
        ]
        ha = next(
            (
                requirement.split("==", 1)[1]
                for requirement in requires or []
                if requirement.startswith("homeassistant==")
            ),
            None,
        )
        releases.append((version, ha))
    return releases


def aiounifi_pin(ha: str) -> str | None:
    """Return the aiounifi requirement of a Home Assistant version."""
    try:
        manifest = get_json(UNIFI_MANIFEST_URL.format(ha=ha))
    except HTTPError:
        return None
    return next(
        (req for req in manifest["requirements"] if req.startswith("aiounifi")),
        None,
    )


def main() -> int:
    """Print the versions."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ha", help="Home Assistant version, e.g. 2026.11.1")
    parser.add_argument(
        "--count", type=int, default=10, help="number of phcc releases to check"
    )
    args = parser.parse_args()

    releases = phcc_releases(args.count)

    if args.ha is None:
        print("phcc       Home Assistant")
        for version, ha in releases:
            print(f"{version:<10} {ha}")
        return 0

    pin = aiounifi_pin(args.ha)
    if pin is None:
        print(f"Home Assistant {args.ha} not found (or without aiounifi requirement)")
        return 1
    aiounifi = pin.split("==", 1)[1]
    print(f"Home Assistant {args.ha} pins {pin}")

    matching = [version for version, ha in releases if ha == args.ha]
    if matching:
        print(f"phcc {matching[0]} pins Home Assistant {args.ha}")
        print(f"  make test PHCC={matching[0]} AIOUNIFI={aiounifi}")
    else:
        print(
            f"No phcc release pins Home Assistant {args.ha} "
            f"(checked the {args.count} newest releases)"
        )
    print(f"  make smoke HA={args.ha} AIOUNIFI={aiounifi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
