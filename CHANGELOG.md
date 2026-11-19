# Changelog

All notable changes to this integration. The section of a version is the
release note of its GitHub release, see [Release process](README.md#release-process).

## [Unreleased]

## [0.1.1] - 2026-11-19

No changes to the integration itself.

### Added

- Pull request check: a pull request to `main` has to raise the version and
  add a changelog section, or be labeled `no-release`
- Merging a pull request into `main` creates the tag and the GitHub release,
  with the changelog section and the commits as release notes
- README: installation from the Home Assistant Marketplace, contributing guide
  and release process

### Changed

- `make test HA=<version>` and `make smoke HA=<version>` look up the matching
  test packages and aiounifi version themselves

## [0.1.0] - 2026-11-19

First release.

### Added

- Switch for every named UniFi Policy Engine rule that the UniFi Network
  integration doesn't provide a switch for
- Switching enables or disables the rule on the UniFi Network application
- Uses the connection of an existing UniFi Network entry, selected in the
  config flow, no own login
- New, changed and removed rules are picked up from the polling of the UniFi
  Network integration, rules move between both integrations when their
  configuration changes
- Follows reloads and unloads of the UniFi Network entry
- Switches are unavailable while the UniFi Network connection is down

### Known limitations

- Rules deleted in UniFi keep their switch until the UniFi Network entry is
  reloaded
- Switches are only created for accounts with the admin role
