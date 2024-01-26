# Hella ONYX.CENTER Custom Component for Home Assistant

[![](https://img.shields.io/github/license/muhlba91/onyx-homeassistant-integration?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/github/actions/workflow/status/muhlba91/onyx-homeassistant-integration/release.yml?style=for-the-badge)](https://github.com/muhlba91/onyx-homeassistant-integration/actions/workflows/release.yml)
[![](https://img.shields.io/coveralls/github/muhlba91/onyx-homeassistant-integration?style=for-the-badge)](https://github.com/muhlba91/onyx-homeassistant-integration/)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![](https://img.shields.io/github/all-contributors/muhlba91/onyx-homeassistant-integration?color=ee8449&style=for-the-badge)](#contributors)
<a href="https://www.buymeacoffee.com/muhlba91" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="28" width="150"></a>

This component creates an integration that provides the following entities to control [Hella's ONYX.CENTER](https://www.hella.info/) via Home Assistant:

- **raffstore/shutter** entities
- **(dimmable) light** entities
- **weather station** sensor entities

---

## Limitations

This integration is under development and based on personal needs and Hella's API design and Home Assistant's
interpretation of values diverges in a few aspects.

Therefore, a few limitations are imposed on/by this integration:

| Limitation | Description| Bound By |
|------------|------------|----------|
| Shutter Position | Home Assistant takes the position 0 as closed and 100 as open, Hella the opposite. | Home Assistant |
| Tilt Position | Home Assistant takes the position 0 as closed and 100 as open, Hella's values range between 0-90 and 0-180. | Home Assistant / Hella |
| Light Brightness | Home Assistant takes the dim value 0 as off and 100 as on, Hella's values range between 0-65535. | Home Assistant / Hella |

### Realtime Updates / Streaming API

Since `v2` of the ONYX API, a dedicated event streaming endpoint is available which pushed occurring events from the
ONYX.CENTER to all clients; however, pushes only include partial updates.

The integration makes use of this and keeps a connection open to the ONYX API server to update the devices in
near-realtime. Since exceptions can occur, and the endpoint only pushes partial updates, all device states are updated
periodically as well to ensure current states are available and correct. Please ensure a proper update interval,
suggested is anywhere between 30-180 minutes.

This integration uses API `v3`.

> [!WARNING]
> The streaming API uses a HTTP GET request which, unfortunately, is timing out and ending the connection every ~10 minutes.
> Currently, the client is reconnecting after a short backoff time.
>
> Hence, errors in your Home Assistant log like `[onyx_client.client] Unexpected exception: ClientPayloadError('Response payload is not completed'). Retrying with backoff Xs.` are to be expected.
>
> The issue is tracked here: <https://github.com/muhlba91/onyx-homeassistant-integration/issues/30>.

---

## Installation

I recommend installation through [HACS](https://hacs.xyz/):

- Ensure HACS is installed.
- Search for and install the `Hella ONYX.CENTER` integration.

### Releases / Versions

The integration offers the following possibilities:

- `main`: the latest stable release
- `v*`: releases following semantic versioning - if you need to pin the version, choose one of those

## Configuration

Add it from the **Integrations menu**, set the configuration, and you're good to go.

| Configuration Key | Description |
|-------------------|-------------|
| API Code | The code retrieved by the ONYX app when allowing a new client to connect. |
| Fingerprint | Your ONYX.CENTER fingerprint. |
| Access Token | The access token. |
| Scan Interval | Interval for polling for updates. This is used as a fallback if near realtime updates are failing and can be set to a higher value. |
| \[Lights] Minimum Dim Duration | The minimum dim duration to use when dimming a light. (Default: 200) |
| Disable partial updates? | The integration relies on the streaming API. Hence, only partial device data will be retrieved. Enable this option to always retrieve the full device data. *Attention*: this may lead to more API requests and is discouraged. |

To configure the integration you can either directly specify a **fingerprint** and an **access token** or use the issued **API code** from the ONYX app directly.
The integration will then exchange this code through the API to retrieve the fingerprint and access token for your ONYX.CENTER.

## Entities

Once configured, the integration creates entities for:

| Entity | Description |
|--------|-------------|
| Cover | Manage the shutter. ([API Reference](https://developers.home-assistant.io/docs/core/entity/cover/)) |
| Light | Manage the (dimmable) light. ([API Reference](https://developers.home-assistant.io/docs/core/entity/light/)) |
| Sensor (Device Type) | The device type of the ONYX device. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Humidity) | The humidity of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Temperature) | The temperature of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Air Pressure) | The air pressure of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Wind Peak) | The wind peak of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Sun Brightness Peak) | The sun brightness peak of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Sun Brightness Sink) | The sun brightness sink of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |

The **following ONYX devices** are **only community tested** due to the lack of a testing device:

- Light (thank you [@clostermannshof](https://github.com/clostermannshof))
- Weather Station (thank you [@mrogin-technic](https://github.com/mrogin-technic))

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

## Contributors

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://muehlbachler.io/"><img src="https://avatars.githubusercontent.com/u/653739?v=4?s=100" width="100px;" alt="Daniel Mühlbachler-Pietrzykowski"/><br /><sub><b>Daniel Mühlbachler-Pietrzykowski</b></sub></a><br /><a href="#maintenance-muhlba91" title="Maintenance">🚧</a> <a href="https://github.com/muhlba91/pulumi-proxmoxve/commits?author=muhlba91" title="Code">💻</a> <a href="https://github.com/muhlba91/pulumi-proxmoxve/commits?author=muhlba91" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/mrogin-technic"><img src="https://avatars.githubusercontent.com/u/20296380?v=4?s=100" width="100px;" alt="mrogin-technic"/><br /><sub><b>mrogin-technic</b></sub></a><br /><a href="#ideas-mrogin-technic" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Jibberchris"><img src="https://avatars.githubusercontent.com/u/121609026?v=4?s=100" width="100px;" alt="Chris Jibber"/><br /><sub><b>Chris Jibber</b></sub></a><br /><a href="#ideas-Jibberchris" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/clostermannshof"><img src="https://avatars.githubusercontent.com/u/151548723?v=4?s=100" width="100px;" alt="Fabian"/><br /><sub><b>Fabian</b></sub></a><br /><a href="#ideas-clostermannshof" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/tbarth64"><img src="https://avatars.githubusercontent.com/u/79904446?v=4?s=100" width="100px;" alt="tbarth64"/><br /><sub><b>tbarth64</b></sub></a><br /><a href="#ideas-tbarth64" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/muhlba91/pulumi-proxmoxve/issues?q=author%3Atbarth64" title="Bug reports">🐛</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!

## Supporting

If you enjoy the application and want to support my efforts, please feel free to buy me a coffe. :)

<a href="https://www.buymeacoffee.com/muhlba91" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="75" width="300"></a>
