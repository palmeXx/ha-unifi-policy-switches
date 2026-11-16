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

### HACS (custom repository)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=palmeXx&repository=ha-unifi-policy-switches&category=integration)

Or manually in HACS:

1. Open HACS in Home Assistant.
2. Open the menu (three dots, top right) and select **Custom repositories**.
3. Add `https://github.com/palmeXx/ha-unifi-policy-switches` with the type
   **Integration**.
4. Search for **UniFi Policy Engine Switches** and download it.
5. Restart Home Assistant.

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
           ├── strings.json
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
   folder and restart Home Assistant. With HACS, remove it in HACS.

## Development

The tests use synthetic rule data only. There are two kinds of test runs:

- **Test suite** (`make test`): the full pytest suite with
  [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
  (phcc). Every phcc release pins exactly one Home Assistant version, the tests
  run on that version.
- **Smoke test** (`make smoke`): imports the integration and checks the rule
  filter against any Home Assistant version, without phcc. Use it for Home
  Assistant versions without a phcc release yet.

Each version combination gets its own virtual environment in the repository
(`.venv-test-*`, `.venv-smoke-*`). It is created on the first run and reused
afterwards. Python 3.14 is used, set `PYTHON=` to use another interpreter.

| Command | Runs |
|---|---|
| `make help` | Overview of the targets |
| `make test-ha2026.10` | Test suite on Home Assistant 2026.10.4 with aiounifi 96 |
| `make smoke-ha2026.11` | Smoke test on Home Assistant 2026.11.1 with aiounifi 98 |
| `make test-all` | Both of the above |
| `make test PHCC=<phcc> AIOUNIFI=<aiounifi>` | Test suite on the Home Assistant version pinned by phcc |
| `make smoke HA=<ha> AIOUNIFI=<aiounifi>` | Smoke test on any Home Assistant version |
| `make test PYTEST_ARGS="-k reload -v"` | Test suite with extra pytest arguments |
| `make versions` | Home Assistant version pinned by the newest phcc releases |
| `make versions HA=<ha>` | aiounifi version pinned by that Home Assistant version and the matching phcc release |
| `make clean` | Remove the virtual environments of the targets |

### Finding matching versions

Home Assistant pins the aiounifi version of the UniFi Network integration in
its manifest, phcc pins the Home Assistant version in its PyPI metadata.
`make versions` looks both up and prints the commands to run:

```console
$ make versions HA=2026.10.4
Home Assistant 2026.10.4 pins aiounifi==96
phcc 0.13.375 pins Home Assistant 2026.10.4
  make test PHCC=0.13.375 AIOUNIFI=96
  make smoke HA=2026.10.4 AIOUNIFI=96

$ make versions HA=2026.11.1
Home Assistant 2026.11.1 pins aiounifi==98
No phcc release pins Home Assistant 2026.11.1 (checked the 10 newest releases)
  make smoke HA=2026.11.1 AIOUNIFI=98
```

Without `HA=` it lists the newest phcc releases, `COUNT=<n>` checks more of
them. To look it up by hand:

- **phcc → Home Assistant:** the `homeassistant==` requirement on
  `https://pypi.org/pypi/pytest-homeassistant-custom-component/<phcc>/json`
  (`info.requires_dist`).
- **Home Assistant → aiounifi:** `requirements` in
  `homeassistant/components/unifi/manifest.json` of the Home Assistant release tag.

Installing a different Home Assistant version than the one pinned by phcc
(`make test HA=...`) is possible, but usually fails, because phcc contains test
helpers copied from that Home Assistant version.

## Disclaimer

This is a community project. It isn't affiliated with, endorsed by or supported
by Ubiquiti Inc. or the Home Assistant project. UniFi is a trademark of
Ubiquiti Inc.

## License

[MIT](LICENSE)
