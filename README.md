# Hella ONYX.CENTER Custom Component for Home Assistant

[![](https://img.shields.io/github/license/muhlba91/onyx-homeassistant-integration?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/github/actions/workflow/status/muhlba91/onyx-homeassistant-integration/release.yml?style=for-the-badge)](https://github.com/muhlba91/onyx-homeassistant-integration/actions/workflows/release.yml)
[![](https://img.shields.io/coveralls/github/muhlba91/onyx-homeassistant-integration?style=for-the-badge)](https://github.com/muhlba91/onyx-homeassistant-integration/)
[![](https://api.scorecard.dev/projects/github.com/muhlba91/onyx-homeassistant-integration/badge?style=for-the-badge)](https://scorecard.dev/viewer/?uri=github.com/muhlba91/onyx-homeassistant-integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![](https://img.shields.io/github/all-contributors/muhlba91/onyx-homeassistant-integration?color=ee8449&style=for-the-badge)](#contributors)
<a href="https://www.buymeacoffee.com/muhlba91" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="28" width="150"></a>

This component creates an integration that provides the following entities to control [Hella's ONYX.CENTER](https://www.hella.info/) via Home Assistant:

- **raffstore/shutter/screen** entities
- **(dimmable) light** entities
- **weather station** sensor entities
- **tag** (ONYX.TAG sun / temperature) sensor entities
- **input** (rain sensor / alarm contact) binary sensor entities
- **software update** entity of the ONYX.CENTER
- **automation** switch entities of the ONYX.CENTER

---

## Limitations

This integration is under development and based on personal needs and Hella's API design and Home Assistant's
interpretation of values diverges in a few aspects.

Therefore, a few limitations are imposed on/by this integration:

| Limitation | Description | Bound By |
| --- | --- | --- |
| Shutter Position | Home Assistant takes the position 0 as closed and 100 as open, Hella the opposite. | Home Assistant |
| Tilt Position | Home Assistant takes the position 0 as closed and 100 as open, Hella's values range between 0-90 and 0-180. | Home Assistant / Hella |
| Light Brightness | Home Assistant takes the dim value 0 as off and 100 as on, Hella's values range between 0-65535. | Home Assistant / Hella |

### Realtime Updates / Streaming API

The integration keeps a connection to the ONYX API's event stream open, which sends the complete state on connect and
changes afterwards. Positions and brightness of moving devices are calculated from the reported animations.
Every scan interval, the stream is reconnected to replace the state with a fresh one from the ONYX.CENTER. A shorter
scan interval corrects deviations sooner but reconnects more often; 30-180 minutes are suggested.
Connection losses are reconnected automatically. If the ONYX.CENTER sends nothing for 90 seconds, for example while
it restarts, the device entities become unavailable until it sends events again. If the stream fails unexpectedly, the
entities become unavailable and the integration restarts the stream every minute until it succeeds.

This integration requires API `v6`. If your ONYX.CENTER does not support it, update its firmware.

Devices removed from the ONYX.CENTER become unavailable; remove them from Home Assistant manually. New devices are
detected automatically; the integration reloads to add their entities.

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

Add it from the **Integrations** menu, set the configuration, and you're good to go.

| Configuration Key | Description |
| --- | --- |
| API Code | The code retrieved by the ONYX app when allowing a new client to connect. |
| Fingerprint | Your ONYX.CENTER fingerprint. |
| Access Token | The access token. |
| Local Address | Your ONYX.CENTER local IP address. |
| Interpolation Frequency | Frequency (in s) to update the position or light intensity while moving. A lower value results in smoother transitions but more updates. Set to 0 to disable interpolation. (Default: 5) |
| Additional Moving Delay | Additional time (in ms) after the end of a movement or dimming during which the device is still shown as moving. (Default: 1000) |
| \[Shutters] Closed Tolerance | Tolerance (in %) within which a shutter counts as closed, as shutters often stop a few percent short of fully closed. (Default: 3) |
| \[Shutters] Moving Timeout | Maximum time (in s) a shutter is shown as opening/closing after a command if the ONYX.CENTER reports no movement. (Default: 180) |
| \[Lights] Minimum Dim Duration | The minimum dim duration (in ms) to use when dimming a light. A range reported by the light itself overrides it. (Default: 200) |
| \[Lights] Maximum Dim Duration | The maximum dim duration (in ms) to use when dimming a light. A range reported by the light itself overrides it. (Default: 2000) |
| Scan Interval | Interval (in min) to reconnect the event stream and replace the state with a fresh one. (Default: 60) |

### Authentication

To configure the integration you can either directly specify a **fingerprint** and an **access token** or use the issued **API code** from the ONYX app directly.

The integration will then exchange this code through the API to retrieve the fingerprint and access token for your ONYX.CENTER.

### Local API Access

To use local API access, you need to provide the local IP address of your ONYX.CENTER device.
Additionally, follow [Authentication](#authentication) to provide the necessary credentials.

If a local address is provided, the integration will always try to connect to the local API.

## Entities

Once configured, the integration creates entities for:

| Entity | Description |
| --- | --- |
| Cover | Manage the shutter, raffstore, awning, pergola or screen. ([API Reference](https://developers.home-assistant.io/docs/core/entity/cover/)) |
| Light | Manage the (dimmable) light. RGBW lights are controlled by brightness only. ([API Reference](https://developers.home-assistant.io/docs/core/entity/light/)) |
| Binary Sensor (Input) | Whether the rain sensor or alarm contact is triggered (for a rain sensor: it is raining). The device class follows the configured role (rain sensor: moisture, fire alarm: smoke, wind or generic alarm: safety). ([API Reference](https://developers.home-assistant.io/docs/core/entity/binary-sensor/)) |
| Button (Identify) | Winks the device to identify it (shutters move a short distance and back, lights blink, other devices light an LED). Disabled by default. ([API Reference](https://developers.home-assistant.io/docs/core/entity/button/)) |
| Switch (Automation) | Enables or disables a safety or comfort automation of the ONYX.CENTER, such as the wind protection; disabling an automation also cancels the commands it issued. Automations without a name, such as the wind protection of a weather sensor, are named after their device if it can be determined, otherwise after their type. The switches belong to the ONYX.CENTER device. Disabled by default (configuration). ([API Reference](https://developers.home-assistant.io/docs/core/entity/switch/)) |
| Update | The software update of the ONYX.CENTER, which can be installed from Home Assistant. An update is offered while the ONYX.CENTER reports one; the ONYX.CENTER checks for updates by itself (the integration never triggers a check), and a newly found update appears with the next reconnect, at the latest after the scan interval. While an update is transferred to the ONYX.CENTER, the entity shows the progress. The entity is unavailable while the ONYX.CENTER reports no update status. ([API Reference](https://developers.home-assistant.io/docs/core/entity/update/)) |
| Sensor (Device Type) | The device type of the ONYX device. For an unsupported device, a diagnostic sensor shows the type reported by the ONYX.CENTER. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (System State) | The calibration and collision state (`ok`, `not_calibrated`, `collision`, `collision_not_calibrated`) of the shutter or pergola, if the device reports it (diagnostic). ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Active Command) | The source type of the command the shutter or light executes (`client`, `automation` or `device`; `unattributed` if the ONYX.CENTER cannot tell the source, `none` while no command is active); the details are attributes, which are not recorded (diagnostic). ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Humidity) | The humidity of the weather sensor or the ONYX.PERGOLA control unit. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Temperature) | The temperature of the weather sensor or the ONYX.PERGOLA control unit. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Air Pressure) | The air pressure of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Wind Peak) | The wind peak of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Wind Speed) | The current wind speed of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Sun Brightness) | The current sun brightness of a sun tag. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Sun Brightness Peak) | The sun brightness peak of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |
| Sensor (Weather Sun Brightness Sink) | The sun brightness sink of the weather sensor. ([API Reference](https://developers.home-assistant.io/docs/core/entity/sensor/)) |

The **following ONYX devices** are **only community tested** due to the lack of a testing device:

- Light (thank you [@clostermannshof](https://github.com/clostermannshof))
- Weather Station (thank you [@mrogin-technic](https://github.com/mrogin-technic))
- Tags (sun, temperature)

The following ONYX devices are **experimental** as they are untested; please report your experience in an issue:

- Screens
- RGBW lights
- Inputs (rain sensors, alarm contacts)
- ONYX.PERGOLA control unit temperature and humidity
- Automation switches

The input binary sensors only report the state of the contact; how the ONYX.CENTER reacts to a triggered contact is configured
on the ONYX.CENTER itself. Do not rely on them as a fire or alarm system.

Disabling a safety automation, such as the wind protection, leaves your shading products unprotected until it is
enabled again. Enable the automation switches only if you need them, and keep them out of automations which could
disable them unintentionally. New automations are detected automatically; the integration reloads to add their
switches. Removed automations become unavailable; remove them from Home Assistant manually.

Installing an update restarts the ONYX.CENTER, which can take several minutes: the devices cannot be controlled, and
their entities become unavailable after 90 seconds without events until it is back. The update entity stays available
and shows the installation in progress until the ONYX.CENTER is back; if it is not back within 30 minutes, a warning is
logged and the progress is reset. Keep the ONYX.CENTER powered during the installation; Home Assistant does not create
a backup of it.

---

## Development

Tool versions (Python, uv, Poetry) are managed with [mise](https://mise.jdx.dev): run `mise trust` and `mise install` once. The project uses [poetry](https://poetry.eustace.io/); to install all dependencies and the build environment, run:

```bash
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

Run mutation testing with `mutmut` by:

```bash
poetry run mutmut run
# check results
poetry run mutmut results
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

## Brand Assets

[Brand assets](custom_components/hella_onyx/brand/) copyright by [HELLA Sonnen- und Wetterschutztechnik GmbH](https://www.hella.info).

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
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/robertweitl"><img src="https://avatars.githubusercontent.com/u/121123263?v=4?s=100" width="100px;" alt="Robert Weitlaner"/><br /><sub><b>Robert Weitlaner</b></sub></a><br /><a href="https://github.com/muhlba91/pulumi-proxmoxve/commits?author=robertweitl" title="Code">💻</a></td>
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
