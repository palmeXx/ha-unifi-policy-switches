"""Release helpers for the pull request check and the release workflow.

  release.py check --base origin/main   version bump and changelog of a pull request
  release.py version --ref 0.2.0        manifest version at a git ref
  release.py notes                      release notes of the working tree version
  release.py notes --ref 0.2.0 --output notes.md

Versions look like 1.2.3, pre-releases like 1.2.3b1 or 1.2.3-rc1. The release
notes are the section of the version in CHANGELOG.md, followed by the commits
since the previous tag. CHANGELOG.md is always read from the working tree.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "custom_components/unifi_policy_switches/manifest.json"
CHANGELOG = ROOT / "CHANGELOG.md"
REPOSITORY_URL = "https://github.com/palmeXx/ha-unifi-policy-switches"

VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:-?(a|alpha|b|beta|rc)\.?(\d+))?")
PRE_RELEASE_ORDER = {"a": 0, "alpha": 0, "b": 1, "beta": 1, "rc": 2}


def git(*args: str) -> str:
    """Run git in the repository and return its output."""
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def version_key(version: str) -> tuple[int, ...]:
    """Sort key of a version, a pre-release sorts before its release."""
    if (match := VERSION.fullmatch(version)) is None:
        raise SystemExit(f"Version {version} isn't like 1.2.3, 1.2.3b1 or 1.2.3-rc1")
    major, minor, patch, pre, pre_number = match.groups()
    if pre is None:
        return (int(major), int(minor), int(patch), 1, 0, 0)
    return (int(major), int(minor), int(patch), 0, PRE_RELEASE_ORDER[pre], int(pre_number))


def manifest_version(ref: str | None = None) -> str | None:
    """Return the manifest version at a git ref, or of the working tree."""
    if ref is None:
        manifest = (ROOT / MANIFEST).read_text()
    else:
        try:
            manifest = git("show", f"{ref}:{MANIFEST}")
        except subprocess.CalledProcessError:
            return None
    return json.loads(manifest)["version"]


def changelog_section(version: str) -> str | None:
    """Return the CHANGELOG.md section of a version, without its heading."""
    match = re.search(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        CHANGELOG.read_text(),
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else None


def tag_exists(version: str) -> bool:
    """Return if a tag of the version exists."""
    return bool(git("tag", "--list", version))


def previous_tag(version: str, ref: str) -> str | None:
    """Return the newest tag before a ref, other than the version itself."""
    try:
        return git("describe", "--tags", "--abbrev=0", f"--exclude={version}", ref)
    except subprocess.CalledProcessError:
        return None


def check(base: str) -> list[str]:
    """Return the problems of the working tree as next release after base."""
    version = manifest_version()
    assert version is not None
    version_key(version)
    problems = []

    base_version = manifest_version(base)
    if base_version is not None and version_key(version) <= version_key(base_version):
        problems.append(
            f"Version {version} in manifest.json has to be greater than "
            f"{base_version} on {base}"
        )
    if tag_exists(version):
        problems.append(f"Tag {version} exists already")
    if not changelog_section(version):
        problems.append(f"CHANGELOG.md needs a section '## [{version}] - <date>'")
    return problems


def build_notes(ref: str | None) -> str:
    """Return the release notes of the version at a ref, or of the working tree."""
    if (version := manifest_version(ref)) is None:
        raise SystemExit(f"Can't read {MANIFEST} at {ref}")
    if not (section := changelog_section(version)):
        raise SystemExit(f"CHANGELOG.md has no section '## [{version}]'")

    head = ref or "HEAD"
    previous = previous_tag(version, head)
    commits = git(
        "log",
        "--no-merges",
        "--pretty=format:- %s (%h)",
        f"{previous}..{head}" if previous else head,
    )
    notes = [section, "", "## Commits", "", commits or "- No commits"]
    if previous:
        notes += ["", f"**Full changelog**: {REPOSITORY_URL}/compare/{previous}...{version}"]
    return "\n".join(notes) + "\n"


def main() -> int:
    """Run a release helper."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    check_parser = commands.add_parser("check", help="check a pull request")
    check_parser.add_argument("--base", required=True, help="git ref of the base")

    version_parser = commands.add_parser("version", help="print manifest version")
    version_parser.add_argument("--ref", help="git ref, the working tree by default")

    notes_parser = commands.add_parser("notes", help="print release notes")
    notes_parser.add_argument("--ref", help="git ref, the working tree by default")
    notes_parser.add_argument("--output", type=Path, help="file for the notes")

    args = parser.parse_args()

    if args.command == "check":
        if problems := check(args.base):
            print("\n".join(f"::error::{problem}" for problem in problems))
            return 1
        print(f"Version {manifest_version()} is ready to be released")
    elif args.command == "version":
        if (version := manifest_version(args.ref)) is None:
            raise SystemExit(f"Can't read {MANIFEST} at {args.ref}")
        version_key(version)
        print(version)
    else:
        notes = build_notes(args.ref)
        if args.output:
            args.output.write_text(notes)
        else:
            print(notes, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
