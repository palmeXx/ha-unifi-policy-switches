"""Look up test versions: phcc releases and the aiounifi pin of Home Assistant.

  versions.py list                  Home Assistant pin of the newest phcc releases
  versions.py show --ha 2026.11.1   aiounifi pin and matching phcc release
  versions.py phcc --ha 2026.10.4   print the phcc release pinning that version
  versions.py aiounifi --ha 2026.10.4
                                    print the aiounifi version it pins
  versions.py newest-ha             print the newest Home Assistant release
  versions.py newest-test-ha        print the newest version with a phcc release

pytest-homeassistant-custom-component (phcc) pins one Home Assistant version per
release in its PyPI metadata, the UniFi integration pins aiounifi in its manifest.
`phcc` and `aiounifi` print only the version, or fail if there is none.
"""

import argparse
from collections.abc import Iterator
import json
import re
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

HA_URL = "https://pypi.org/pypi/homeassistant/json"
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
    """Sort key of the numeric parts of a version, 2026.11.0b1 sorts as 2026.11.0."""
    return tuple(int(part) for part in re.findall(r"\d+", version)[:3])


def phcc_releases() -> Iterator[tuple[str, str | None]]:
    """Yield phcc releases with their Home Assistant pin, newest first."""
    versions = sorted(get_json(PHCC_URL)["releases"], key=version_key, reverse=True)
    for version in versions:
        requires = get_json(PHCC_VERSION_URL.format(version=version))["info"][
            "requires_dist"
        ]
        yield version, next(
            (
                requirement.split("==", 1)[1]
                for requirement in requires or []
                if requirement.startswith("homeassistant==")
            ),
            None,
        )


def find_phcc(ha: str) -> str | None:
    """Return the phcc release pinning a Home Assistant version."""
    for version, pinned in phcc_releases():
        if pinned == ha:
            return version
        # Releases pin newer Home Assistant versions the newer they are
        if pinned is not None and version_key(pinned) < version_key(ha):
            return None
    return None


def newest_test_ha() -> str | None:
    """Return the newest Home Assistant version with a phcc release."""
    return next((ha for _, ha in phcc_releases() if ha is not None), None)


def aiounifi_pin(ha: str) -> str | None:
    """Return the aiounifi version pinned by a Home Assistant version."""
    try:
        manifest = get_json(UNIFI_MANIFEST_URL.format(ha=ha))
    except HTTPError:
        return None
    return next(
        (
            requirement.split("==", 1)[1]
            for requirement in manifest["requirements"]
            if requirement.startswith("aiounifi==")
        ),
        None,
    )


def main() -> int:
    """Run a lookup."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    list_parser = commands.add_parser("list", help="newest phcc releases")
    list_parser.add_argument("--count", type=int, default=10)
    for command in ("show", "phcc", "aiounifi"):
        commands.add_parser(command).add_argument("--ha", required=True)
    commands.add_parser("newest-ha", help="newest Home Assistant release")
    commands.add_parser("newest-test-ha", help="newest version with phcc release")
    args = parser.parse_args()

    if args.command == "newest-ha":
        # PyPI reports the newest release without pre-releases
        print(get_json(HA_URL)["info"]["version"])
        return 0

    if args.command == "newest-test-ha":
        if (ha := newest_test_ha()) is None:
            print("No phcc release pins a Home Assistant version", file=sys.stderr)
            return 1
        print(ha)
        return 0

    if args.command == "list":
        print("phcc       Home Assistant")
        for _, (version, ha) in zip(range(args.count), phcc_releases(), strict=False):
            print(f"{version:<10} {ha}")
        return 0

    if args.command == "phcc":
        if (phcc := find_phcc(args.ha)) is None:
            print(
                f"No pytest-homeassistant-custom-component release pins Home "
                f"Assistant {args.ha}, use: make smoke HA={args.ha}",
                file=sys.stderr,
            )
            return 1
        print(phcc)
        return 0

    aiounifi = aiounifi_pin(args.ha)
    if args.command == "aiounifi":
        if aiounifi is None:
            print(
                f"Home Assistant {args.ha} not found, or its UniFi integration "
                "doesn't pin aiounifi",
                file=sys.stderr,
            )
            return 1
        print(aiounifi)
        return 0

    if aiounifi is None:
        print(f"Home Assistant {args.ha} not found")
        return 1
    print(f"Home Assistant {args.ha} pins aiounifi {aiounifi}")
    if phcc := find_phcc(args.ha):
        print(f"phcc {phcc} pins Home Assistant {args.ha}")
        print(f"  make test HA={args.ha}")
    else:
        print(f"No phcc release pins Home Assistant {args.ha}")
    print(f"  make smoke HA={args.ha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
