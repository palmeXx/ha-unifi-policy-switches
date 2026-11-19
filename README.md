# UniFi Policy Engine Switches

A Home Assistant custom integration that adds a switch for **every** UniFi Policy
Engine rule (object-oriented network config), not only the rules blocking internet
access.

The built-in [UniFi Network](https://www.home-assistant.io/integrations/unifi/)
integration only creates switches for Policy Engine rules that turn off internet
access. This integration fills the gap: it docks onto your existing UniFi Network
integration, reuses its connection and adds switches for all other named rules,
such as QoS or routing rules. It doesn't replace or override the UniFi Network
integration, both run side by side.

## Features

- One switch per Policy Engine rule not covered by the UniFi Network integration
- Switching enables or disables the rule on the UniFi Network application
- No own login: the connection of the UniFi Network integration is used
- New, changed and removed rules are picked up automatically
- Rules move between both integrations when their configuration changes, so a
  rule never gets two switches
- Switches are unavailable while the UniFi Network connection is down

## Requirements

- Home Assistant 2026.10 or newer
- The [UniFi Network](https://www.home-assistant.io/integrations/unifi/)
  integration, set up with an account having the **admin** role on the site.
  Like the switches of the UniFi Network integration, no switches are created
  for accounts without admin rights. See [Checking the admin role](#checking-the-admin-role).
- A UniFi Network application with Policy Engine (object-oriented network configs)

### Checking the admin role

The UniFi Network integration only treats the account as admin if the UniFi
Network application reports the role `admin` for the configured site. Which
roles of the UniFi user management map to it isn't documented by Ubiquiti, so
check it in Home Assistant:

1. Go to **Settings** → **Devices & services** → **UniFi Network**.
2. Open the menu (three dots) of the entry and select **Download diagnostics**.
3. Search the downloaded JSON file for `role_is_admin`, it has to be `true`.

The role is read when the UniFi Network entry is loaded. After changing the role
in UniFi, reload the UniFi Network entry, this integration follows
automatically. The diagnostics file is redacted by Home Assistant, but still
contains details of your network, check it before sharing it.

## Installation

### Marketplace (Home Assistant 2026.11 and newer)

Since Home Assistant 2026.11, HACS is built in as the **Marketplace**. Until this
integration is in the catalog, add it from its link:

1. Go to **Settings** → **Marketplace**.
2. Select **Add from link** and enter `palmeXx/ha-unifi-policy-switches`.
   Adding a repository from a link needs a GitHub connection, Home Assistant
   asks for it the first time.
3. Install **UniFi Policy Engine Switches**.
4. Restart Home Assistant when asked.

### HACS (Home Assistant 2026.10)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=palmeXx&repository=ha-unifi-policy-switches&category=integration)

Or manually in HACS:

1. Open HACS in Home Assistant.
2. Open the menu (three dots, top right) and select **Custom repositories**.
3. Add `https://github.com/palmeXx/ha-unifi-policy-switches` with the type
   **Integration**.
4. Search for **UniFi Policy Engine Switches** and download it.
5. Restart Home Assistant.

When updating to Home Assistant 2026.11, HACS content is moved to the
Marketplace automatically.

### Manual installation

1. Download the latest release from the
   [releases page](https://github.com/palmeXx/ha-unifi-policy-switches/releases)
   and extract it, or clone the repository:

   ```shell
   git clone https://github.com/palmeXx/ha-unifi-policy-switches.git
   ```

2. Copy the folder `custom_components/unifi_policy_switches` into the
   `custom_components` folder of your Home Assistant configuration directory
   (the folder containing `configuration.yaml`). Create `custom_components` if it
   doesn't exist yet. The result has to look like this:

   ```text
   <config>/
   ├── configuration.yaml
   └── custom_components/
       └── unifi_policy_switches/
           ├── __init__.py
           ├── brand/
           ├── config_flow.py
           ├── const.py
           ├── manifest.json
           ├── switch.py
           └── translations/
   ```

   You can copy the files with the Samba share, SSH or File editor add-ons, or
   any other way you access the configuration directory.

3. Restart Home Assistant.

To update a manual installation, replace the `unifi_policy_switches` folder with
the one of the new release and restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & services** → **Add integration**.
2. Search for **UniFi Policy Engine Switches**.
3. Select the UniFi Network entry to use.

Each UniFi Network entry can be used once. The switches are added to the
**UniFi Network** service device, next to the Policy Engine switches of the UniFi
Network integration, and are listed as configuration entities. The entity names
follow the rule names in UniFi.

## How it works

- The UniFi Network integration polls the Policy Engine rules every 10 seconds
  (every 10 minutes while there are no rules). This integration reacts to these
  updates and doesn't poll on its own, so changes made in UniFi show up within
  about 10 seconds.
- A rule gets a switch here if it has a name and the UniFi Network integration
  doesn't create a switch for it. The UniFi Network integration handles rules
  with an enabled internet block (`TURN_OFF_INTERNET`).
- When the UniFi Network entry is reloaded, unloaded or not ready yet, this
  integration follows it and reloads as well.

## Known limitations

- **Deleted rules:** The UniFi Network integration doesn't report rules deleted in
  UniFi while it is running. Their switches stay until the UniFi Network entry is
  reloaded or Home Assistant is restarted. Afterwards, remove the leftover entity
  in the entity settings.
- **Rules without a name** are skipped.
- This integration relies on internals of the UniFi Network integration, which
  aren't a public API. A Home Assistant update can break it until a new release
  of this integration follows.

## Removal

1. Go to **Settings** → **Devices & services** → **UniFi Policy Engine Switches**.
2. Open the menu of the entry and select **Delete**.
3. For a manual installation, remove the `custom_components/unifi_policy_switches`
   folder and restart Home Assistant. Otherwise remove it in the Marketplace
   or in HACS.

## Contributing

Contributions are welcome: bug reports and ideas as
[issues](https://github.com/palmeXx/ha-unifi-policy-switches/issues), changes
as pull requests. Every pull request to `main` is the next release, merging it
publishes it.

1. For larger changes, open an issue first to agree on the approach.
2. Fork the repository and create a branch from `main`.
3. Make the change and add or update tests, then run them, see
   [Development](#development):

   ```shell
   make test HA=2026.10.4
   make smoke HA=2026.11.1
   ```

   Use the newest Home Assistant version with a test suite release for `test`,
   and the current Home Assistant version for `smoke`, `make versions` lists them.

4. Decide if the pull request is a release:
   - **Changes of the integration** are released. Raise `version` in
     `manifest.json` and add a `CHANGELOG.md` section for it, see
     [Release process](#release-process). Check both with
     `make release-check` and preview the release notes with
     `make release-notes`.
   - **Other changes**, like the README, the workflows or only tests, are not
     released. Keep the version, the maintainer labels the pull request
     `no-release`. Only users with write access can set labels, mention it in
     the pull request.

   If you're unsure, ask in the pull request.
5. Open the pull request against `main`. The checks `Release check`,
   `HACS validation`, `Hassfest validation` and `pytest` have to pass.
6. After the review, the maintainer merges the pull request, which creates the
   tag and the GitHub release automatically.

Use synthetic data only. Don't put real details of your network, like rule
names, IDs, MAC or IP addresses, into tests, issues or shared logs and
diagnostics.

### Development

The tests use synthetic rule data only. There are two kinds of test runs, both
for a Home Assistant version set with `HA=`:

- **Test suite** (`make test HA=<version>`): the full pytest suite with
  [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
  (phcc). Every phcc release pins exactly one Home Assistant version. `make test`
  looks up the phcc release of the given version first and stops if there is
  none.
- **Smoke test** (`make smoke HA=<version>`): imports the integration and
  checks the rule filter, without phcc. It works with any Home Assistant
  version, also with one that has no phcc release yet.

Both use the aiounifi version that the UniFi Network integration of that Home
Assistant version pins, unless `AIOUNIFI=` is set.

| Command | Runs |
|---|---|
| `make help` | Overview of the targets |
| `make test HA=<ha>` | Test suite on that Home Assistant version |
| `make smoke HA=<ha>` | Smoke test on that Home Assistant version |
| `make test HA=<ha> AIOUNIFI=<aiounifi>` | Same, with another aiounifi version, also for `smoke` |
| `make test HA=<ha> PYTEST_ARGS="-k reload -v"` | Test suite with extra pytest arguments |
| `make versions` | Home Assistant version pinned by the newest phcc releases, `COUNT=<n>` for more |
| `make versions HA=<ha>` | aiounifi version and phcc release of that Home Assistant version |
| `make clean` | Remove the virtual environments of the targets |

Each version combination gets its own virtual environment in the repository
(`.venv-test-*`, `.venv-smoke-*`). The versions are looked up online when it is
created, later runs reuse it offline. Python 3.14 is used, set `PYTHON=` to use
another interpreter.

#### Finding matching versions

Home Assistant pins the aiounifi version of the UniFi Network integration in
its manifest, phcc pins the Home Assistant version in its PyPI metadata.
`make versions` looks both up:

```console
$ make versions HA=2026.10.4
Home Assistant 2026.10.4 pins aiounifi 96
phcc 0.13.375 pins Home Assistant 2026.10.4
  make test HA=2026.10.4
  make smoke HA=2026.10.4

$ make versions HA=2026.11.1
Home Assistant 2026.11.1 pins aiounifi 98
No phcc release pins Home Assistant 2026.11.1
  make smoke HA=2026.11.1
```

To look it up by hand:

- **phcc → Home Assistant:** the `homeassistant==` requirement on
  `https://pypi.org/pypi/pytest-homeassistant-custom-component/<phcc>/json`
  (`info.requires_dist`).
- **Home Assistant → aiounifi:** `requirements` in
  `homeassistant/components/unifi/manifest.json` of the Home Assistant release tag.

### Release process

Every pull request to `main` is the next release, merging it releases it.

1. In the pull request, raise `version` in
   `custom_components/unifi_policy_switches/manifest.json`, following
   [semantic versioning](https://semver.org/). Pre-releases look like `0.2.0b1`
   or `0.2.0-rc1`.
2. Move the entries of `## [Unreleased]` in `CHANGELOG.md` into a new section
   `## [<version>] - <date>`. This section is the release note.
3. The `Release check` of the pull request fails if the version isn't greater
   than on `main`, its tag exists already or `CHANGELOG.md` has no section for
   it. Check it before pushing with `make release-check` and preview the notes
   with `make release-notes`.
4. Merge the pull request. The `Release` workflow validates and tests `main`,
   then creates the tag and the GitHub release. Nothing else to do.

Pull requests that shouldn't be released, like changes of the README or the
workflows, get the label `no-release`. They skip the release check and their
merge creates no release.

The release notes are the `CHANGELOG.md` section, followed by the commits since
the previous tag. Pre-releases are only offered to Marketplace users who opt in.

Pushing a tag yourself still works: it has to match the manifest version, and
the workflow creates the release for it. For a tag pushed before the workflow
existed, or to update the notes of a release, run the `Release` workflow
manually with the tag (Actions → Release → Run workflow). It then uses
`CHANGELOG.md` of the branch it runs on.

To enforce the check, protect `main` in the repository settings (Settings →
Rules → Rulesets, or Branches): require a pull request before merging and the
status checks `Release check`, `HACS validation`, `Hassfest validation` and
`pytest`.

## Disclaimer

This is a community project. It isn't affiliated with, endorsed by or supported
by Ubiquiti Inc. or the Home Assistant project. UniFi is a trademark of
Ubiquiti Inc.

## License

[MIT](LICENSE)
