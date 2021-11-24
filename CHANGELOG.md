# Changelog


## [2.0.0-beta.3](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v2.0.0-beta.2...v2.0.0-beta.3) (2021-11-24)

## [2.0.0-beta.2](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v2.0.0-beta.1...v2.0.0-beta.2) (2021-11-22)


### Bug Fixes

* bump onyx-client to 3.0.4; filter unknown devices ([58c1c7b](https://github.com/muhlba91/onyx-homeassistant-integration/commit/58c1c7b6d95a8eda0a804018d6561fe5b2056863))

## [2.0.0-beta.1](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v2.0.0-beta.0...v2.0.0-beta.1) (2021-11-22)


### Bug Fixes

* bump onyx-client to 3.0.2; related to [#8](https://github.com/muhlba91/onyx-homeassistant-integration/issues/8) ([c5af543](https://github.com/muhlba91/onyx-homeassistant-integration/commit/c5af543fffbb23b81528ab1ec582b0096a3ace56))

## [2.0.0-beta.0](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v1.2.0...v2.0.0-beta.0) (2021-11-22)


### ⚠ BREAKING CHANGES

* fix #9

### Features

* prepare for api v3 ([3a952b0](https://github.com/muhlba91/onyx-homeassistant-integration/commit/3a952b0ebbf0470086fd1d0abdc3f3d3aadb1e26))
* upgrade to API v3; fix [#9](https://github.com/muhlba91/onyx-homeassistant-integration/issues/9) ([be5547e](https://github.com/muhlba91/onyx-homeassistant-integration/commit/be5547ed244f3ae8153b8f87330e001ed53fb1c0))


### Bug Fixes

* detect cover position according to hella and home assistant requirements; fix [#9](https://github.com/muhlba91/onyx-homeassistant-integration/issues/9) ([251b9cd](https://github.com/muhlba91/onyx-homeassistant-integration/commit/251b9cd2120b5957487de65fa8acdcf08f377f07))
* filter entities, fix state detection, add property to enforce getting all data; [#9](https://github.com/muhlba91/onyx-homeassistant-integration/issues/9) ([b4866fd](https://github.com/muhlba91/onyx-homeassistant-integration/commit/b4866fd48bc415fd3020a298be625063107936b2))

## [1.2.0](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v1.1.0...v1.2.0) (2021-02-14)


### Features

* use realtime events listener ([500e4d2](https://github.com/muhlba91/onyx-homeassistant-integration/commit/500e4d2087adb5401ca6624b2416d862de554f31))


### Bug Fixes

* restart event processing, fix [#7](https://github.com/muhlba91/onyx-homeassistant-integration/issues/7) ([c3f7f2f](https://github.com/muhlba91/onyx-homeassistant-integration/commit/c3f7f2f14dcab682bdc4379a1b8ef691e54da8d2))
* set connection timeouts to indefinite ([32996fb](https://github.com/muhlba91/onyx-homeassistant-integration/commit/32996fb419a149437e07fd99cfbec8b7a2af7e3c))

## 1.1.0 (2021-02-12)


### Features

* add sensors, fix [#1](https://github.com/muhlba91/onyx-homeassistant-integration/issues/1) ([c615307](https://github.com/muhlba91/onyx-homeassistant-integration/commit/c6153074839e31dbbf7847ad430597a7bc12f745))
* include drive direction analysis ([944f27b](https://github.com/muhlba91/onyx-homeassistant-integration/commit/944f27be7854194033297644d1bc59a866ce27d6))
* increase update interval ([d841341](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d841341363e215798c05b0a0001e0f662d88af0e))
* initial poc ([319dc7f](https://github.com/muhlba91/onyx-homeassistant-integration/commit/319dc7f1bc90083355bc8ac8cf7be789fdb4c078))


### Bug Fixes

* drivetime up and down ([959e8a9](https://github.com/muhlba91/onyx-homeassistant-integration/commit/959e8a966f0e09d99b787fef576cc595e603da3a))
