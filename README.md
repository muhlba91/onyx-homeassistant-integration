# Hella ONYX.CENTER Custom Component for Home Assistant

[![](https://img.shields.io/github/license/muhlba91/onyx-homeassistant-integration?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/github/actions/workflow/status/muhlba91/onyx-homeassistant-integration/release.yml?style=for-the-badge)](https://github.com/muhlba91/onyx-homeassistant-integration/actions/workflows/release.yml)
[![](https://img.shields.io/coveralls/github/muhlba91/onyx-homeassistant-integration?style=for-the-badge)](https://github.com/muhlba91/onyx-homeassistant-integration/)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Known Vulnerabilities](https://snyk.io/test/github/muhlba91/onyx-homeassistant-integration/badge.svg)](https://snyk.io/test/github/muhlba91/onyx-homeassistant-integration)
<a href="https://www.buymeacoffee.com/muhlba91" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="28" width="150"></a>

This component creates an integration that provides the following entities to control [Hella's ONYX.CENTER](https://www.hella.info/) via Home Assistant:

- **raffstore/shutter** entities
- **weather station** sensor entities

---

## Limitations

This integration is under development and based on personal needs and Hella's API design and Home Assistant's
interpretation of values diverges in a few aspects.

Therefore, a few limitations are imposed on/by this integration:

| Limitation                               | Description                                                                                                                                         | Bound By               |
|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|
| Fingerprint, Access Token Authentication | The API requires the ONYX.CENTER fingerprint and an access token. Basically, those can be retrieved programmatically, which is not implemented yet. | Personal Needs         |
| Shutter Position                         | Home Assistant takes the position 0 as closed and 100 as open, Hella the opposite.                                                                  | Home Assistant         |
| Tilt Position                            | Home Assistant takes the position 0 as closed and 100 as open, Hella's values range between 0-90 and 0-180.                                         | Home Assistant / Hella |

### Realtime Updates / Streaming API

Since `v2` of the ONYX API, a dedicated event streaming endpoint is available which pushed occurring events from the
ONYX.CENTER to all clients; however, pushes only include partial updates.

The integration makes use of this and keeps a connection open to the ONYX API server to update the devices in
near-realtime. Since exceptions can occur, and the endpoint only pushes partial updates, all device states are updated
periodically as well to ensure current states are available and correct. Please ensure a proper update interval,
suggested is anywhere between 30-180 minutes.

This integration uses API `v3`.

## Installation

I recommend installation through [HACS](https://hacs.xyz/):

- Ensure HACS is installed.
- Search for and install the `Hella ONYX.CENTER` integration.

### Releases / Versions

The integration offers the following possibilities:

- `main`: the latest stable release
- `next`: the next, cutting-edge release (**attention**: may be unstable)
- `v*`: releases following semantic versioning - if you need to pin the version, choose one of those

## Configuration

Add it from the **Integrations menu**, set the configuration, and you're good to go.

| Configuration Key        | Description                                                                                                                                                                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Fingerprint              | Your ONYX.CENTER fingerprint (see below).                                                                                                                                                                                       |
| Access Token             | The access token (see below).                                                                                                                                                                                                   |
| Scan Interval            | Interval for polling for updates. This is used as a fallback if near realtime updates are failing and can be set to a higher value.                                                                                             |
| Disable partial updates? | The integration relies on the streaming API. Hence, only partial device data will be retrieved. Enable this option to always retrieve the full device data. *Attention*: this may lead to more API requests and is discouraged. |

**Important!** Please read **[ONYX.CENTER API's Access Control](https://github.com/hella-info/onyx_api#access-control)**
on how to retrieve the **fingerprint** and **access token**.

Once configured, the integration **creates entities** for:

| Entity               | Description                                                                                                      |
|----------------------|------------------------------------------------------------------------------------------------------------------|
| Cover                | Manage the shutter. ([API Reference](https://developers.home-assistant.io/docs/core/entity/cover/))              |
| Light                | Manage the (dimmable) light. ([API Reference](https://developers.home-assistant.io/docs/core/entity/light/))              |
| Sensor (Device Type) | The device type of the ONYX device. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Humidity) | The humidity of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Temperature) | The temperature of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Air Pressure) | The air pressure of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Wind Peak) | The wind peak of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Sun Brightness Peak) | The sun brightness peak of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Sun Brightness Sink) | The sun brightness sink of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |

---

## Development

The project uses [poetry](https://poetry.eustace.io/) and to install all dependencies and the build environment, run:

```bash
pip install poetry
poetry install
```

### Testing

1) Install all dependencies as shown above.
2) Run `pytest` by:

```bash
poetry run pytest
# or
pytest
```

### Linting and Code Style

The project uses [ruff](https://github.com/astral-sh/ruff) for automated code linting and fixing, also using [pre-commit](https://pre-commit.com/).

1) Install all dependencies as shown above.
2) (Optional) Install pre-commit hooks:

```bash
poetry run pre-commit install
```

3) Run ruff:

```bash
poetry run ruff check .
# poetry run ruff format .
```

### Commit Message

This project follows [Conventional Commits](https://www.conventionalcommits.org/), and your commit message must also
adhere to the additional rules outlined in `.conform.yaml`.

---

## Contributions

Please feel free to contribute, be it with Issues or Pull Requests! Please read
the [Contribution guidelines](CONTRIBUTING.md)

## Supporting

If you enjoy the application and want to support my efforts, please feel free to buy me a coffe. :)

<a href="https://www.buymeacoffee.com/muhlba91" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="75" width="300"></a>
