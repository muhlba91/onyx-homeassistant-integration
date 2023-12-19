# Changelog


## [9.0.0](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v8.0.0...v9.0.0) (2023-12-19)


### Features

* implement automated exchange of API code to fingerprint and token; fix [#6](https://github.com/muhlba91/onyx-homeassistant-integration/issues/6) ([71814c3](https://github.com/muhlba91/onyx-homeassistant-integration/commit/71814c39b9b3f1adb06313336da3151b928ebff5))


### Miscellaneous Chores

* set next release to 9.0.0 ([19eb1b0](https://github.com/muhlba91/onyx-homeassistant-integration/commit/19eb1b0c9d7c73988bc9f3197e5e6670011afb56))

## [8.0.0](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v7.0.0...v8.0.0) (2023-12-18)


### ⚠ BREAKING CHANGES

* uses the client event loop for event updates

### Features

* add configuration for dim durations ([961cc74](https://github.com/muhlba91/onyx-homeassistant-integration/commit/961cc74a4f52c736829d37b3ec4d4ba71a2420c5))
* add options config flow ([e37ae4d](https://github.com/muhlba91/onyx-homeassistant-integration/commit/e37ae4dd56452afc9322c47a947c0d262fce0d85))
* add support for lights ([8839c3c](https://github.com/muhlba91/onyx-homeassistant-integration/commit/8839c3cc1efe35ddf13b77a931cbc9460161faf0))
* ignore devices without device type; update client to 8.1.0 ([a805145](https://github.com/muhlba91/onyx-homeassistant-integration/commit/a8051456028962dc8980c757eb14c0af4ab6a227))
* replace event thread with coordinator and background task ([fe3f7ea](https://github.com/muhlba91/onyx-homeassistant-integration/commit/fe3f7eab846f1ac521992c82500d9332ffc431a5))
* replace linters with ruff ([cd58021](https://github.com/muhlba91/onyx-homeassistant-integration/commit/cd5802153a21b48b725b4f869f67525976f622d7))


### Bug Fixes

* add __str__ for configuration and add debug log ([4659ee3](https://github.com/muhlba91/onyx-homeassistant-integration/commit/4659ee3a097d4b52db880bfaaa1fbcb843fbf2e4))
* add entry migration ([5720bcd](https://github.com/muhlba91/onyx-homeassistant-integration/commit/5720bcdbeff8a8e26e6121f1e35e3d8b9d86e1c3))
* add entry migration ([f4402c5](https://github.com/muhlba91/onyx-homeassistant-integration/commit/f4402c50f5bd27bc9d80bb7fc668b2aa7831f7d2))
* add light device sensor ([3b88d64](https://github.com/muhlba91/onyx-homeassistant-integration/commit/3b88d64e545956bff8dfffb40bf4f38454f87cd4))
* add light platform ([d835172](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d8351720e10ac19aa5530bc5791917d724fc9344))
* add tests for config flow ([c43a8e6](https://github.com/muhlba91/onyx-homeassistant-integration/commit/c43a8e6c473d0e71590494a2169595cbfaa84494))
* add translations for configs ([d8bc6ba](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d8bc6ba8a5c0e5111e72ba01a163b4ab4336efc9))
* call ha state update ([a408da3](https://github.com/muhlba91/onyx-homeassistant-integration/commit/a408da3a1776a2b637d63dc79153a811c7c20b47))
* call light_on if no brightness is specified ([4c72d54](https://github.com/muhlba91/onyx-homeassistant-integration/commit/4c72d54e627d1b2f3de08a99498243b9f920a454))
* change update method to onyx api client ([53a957f](https://github.com/muhlba91/onyx-homeassistant-integration/commit/53a957feb8708ba919aa573b7e2de1150d739450))
* do not trigger background action for finished animations ([7812e24](https://github.com/muhlba91/onyx-homeassistant-integration/commit/7812e2421dbb577d11112e43c7bf2e4ba7f2364a))
* fix dim duration calculation; update client to 8.3.3 to fix numeric value defaults ([cf2042d](https://github.com/muhlba91/onyx-homeassistant-integration/commit/cf2042d68aba913abad5f2bcd6c75a49347d7d59))
* fix light supported_features return value ([f3af412](https://github.com/muhlba91/onyx-homeassistant-integration/commit/f3af4120358370ba019a8e4b179d9de297cb7a07))
* fix stop call ([6117eec](https://github.com/muhlba91/onyx-homeassistant-integration/commit/6117eec38a25fe15e9d4847e36bb9f239fd03571))
* handle animation for lights ([935bc41](https://github.com/muhlba91/onyx-homeassistant-integration/commit/935bc41b528a4a7d6f5d607435d72c67de5e419c))
* handle no brightness value; correctly feed on/off to home assistant ([90066fc](https://github.com/muhlba91/onyx-homeassistant-integration/commit/90066fc0c16f647be8611c9f6d55ede62e6c2bb4))
* ignore invalid brightness value for dim duration ([839c57b](https://github.com/muhlba91/onyx-homeassistant-integration/commit/839c57bfaeeea7d40730a61249054657b8d49eb4))
* ignore outdated animations ([f5f01d5](https://github.com/muhlba91/onyx-homeassistant-integration/commit/f5f01d5ba1f807dd92b5ad499a808b0152c9015c))
* ignore outdated animations ([f41452d](https://github.com/muhlba91/onyx-homeassistant-integration/commit/f41452d0beaa7e1a64a7221eea8b682a537828cc))
* interpolate updates instead of dropping old ones ([28bc0ce](https://github.com/muhlba91/onyx-homeassistant-integration/commit/28bc0ceee01bffc89fff739663e305902d33a27c))
* interpolate updates instead of dropping old ones ([050d52c](https://github.com/muhlba91/onyx-homeassistant-integration/commit/050d52cd45b1470a011b1ad85c63e11a629e4701))
* reduce backoff time for reconnects ([d5cd07f](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d5cd07fa74f35d4de3cfe71cdbfa89713aee2076))
* refactor dimming and moving updates ([dcfc299](https://github.com/muhlba91/onyx-homeassistant-integration/commit/dcfc29996629cc868c0a066a4d83633e84808bec))
* reload entry on configuration change ([75581b5](https://github.com/muhlba91/onyx-homeassistant-integration/commit/75581b5ea328317a8a5c884be3cbaaf616bf6e78))
* set defaults for new config ([54764fd](https://github.com/muhlba91/onyx-homeassistant-integration/commit/54764fdafb4a6c147d30657cf8f19ec39ed78bdd))
* set dim duration correctly; add tests for dim duration variations ([8f70612](https://github.com/muhlba91/onyx-homeassistant-integration/commit/8f70612fa892863ed6f16c11c443e1ab19db70f8))
* set event loop for client ([4a1cb81](https://github.com/muhlba91/onyx-homeassistant-integration/commit/4a1cb8105afaebcf8783fff17fbabf1d952406e2))
* set event loop for client ([b20c729](https://github.com/muhlba91/onyx-homeassistant-integration/commit/b20c729a251eb0adda28e93d15a91681092356d4))
* set event loop for client ([e0f8943](https://github.com/muhlba91/onyx-homeassistant-integration/commit/e0f89430e3d2347a803f74bc5d0aeef07a3432ea))
* set event loop for client ([4ab1e3b](https://github.com/muhlba91/onyx-homeassistant-integration/commit/4ab1e3b498bf72566f5acf6501362554077f3df4))
* set event loop for client ([3042cf4](https://github.com/muhlba91/onyx-homeassistant-integration/commit/3042cf417784eb92154087a9471330160fa884bc))
* set event loop for client ([b7e94a3](https://github.com/muhlba91/onyx-homeassistant-integration/commit/b7e94a309eddb9e87747223109450eac83238e58))
* set event loop for client ([b5e3fae](https://github.com/muhlba91/onyx-homeassistant-integration/commit/b5e3faea662abcd75ad65861c49281e7cdef1cdc))
* set event loop for client ([45b1d6b](https://github.com/muhlba91/onyx-homeassistant-integration/commit/45b1d6b199caaea74779810d5c6483c6fb6a23b7))
* set hassio event loop for client ([2378b19](https://github.com/muhlba91/onyx-homeassistant-integration/commit/2378b193afb527dc1652656af586d0ec43e08fa7))
* update client to 8.3.1 to implement deep merge ([c87ca95](https://github.com/muhlba91/onyx-homeassistant-integration/commit/c87ca954a09800668af745b31633f0244102d99f))


### Miscellaneous Chores

* adapt logging ([891a124](https://github.com/muhlba91/onyx-homeassistant-integration/commit/891a1245117a866d5ece8e6871ca00ebab6e2035))
* **ci:** adopt release please for v4 ([989cf78](https://github.com/muhlba91/onyx-homeassistant-integration/commit/989cf780075f3ab5b144ec3c9a6c9693c10c6029))
* clean shutter moving log ([d197388](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d19738853251aef3ba704af20853ca602062d977))
* **deps:** update actions/setup-python action to v5 ([2f24df3](https://github.com/muhlba91/onyx-homeassistant-integration/commit/2f24df3cf00ea87c8d819d6aec8c11a7ffbc63c7))
* **deps:** update client to 8.0.2 ([34103e2](https://github.com/muhlba91/onyx-homeassistant-integration/commit/34103e262b7fd6b9992b7b61b485213414d9fd2c))
* **deps:** update dependency aioresponses to v0.7.6 ([ee0fe43](https://github.com/muhlba91/onyx-homeassistant-integration/commit/ee0fe4383581a888ea57501f1fec5d73df6fdbb8))
* **deps:** update dependency homeassistant to v2023.12.0 ([44e184e](https://github.com/muhlba91/onyx-homeassistant-integration/commit/44e184e2d3bb3e14330aa27cbce4498ad3a1f5bc))
* **deps:** update dependency homeassistant to v2023.12.2 ([d0710ed](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d0710ed486aff444875fa2f777ebc3d414062322))
* **deps:** update dependency pre-commit to v3.6.0 ([32c4fc2](https://github.com/muhlba91/onyx-homeassistant-integration/commit/32c4fc282bb0c2a3a217d5b76cf8d10d841d148a))
* **deps:** update dependency pytest-asyncio to ^0.23.0 ([1151786](https://github.com/muhlba91/onyx-homeassistant-integration/commit/11517862939e83ab37bbf03385bfc46d6308de10))
* **deps:** update dependency pytest-asyncio to v0.23.1 ([dce3062](https://github.com/muhlba91/onyx-homeassistant-integration/commit/dce3062fa712d45bfc3d2cc790c7089fae78ae6a))
* **deps:** update dependency pytest-asyncio to v0.23.2 ([debfe61](https://github.com/muhlba91/onyx-homeassistant-integration/commit/debfe61edd6eaedc9991ad07e7f0d386ef777901))
* **deps:** update dependency ruff to v0.1.7 ([b533be2](https://github.com/muhlba91/onyx-homeassistant-integration/commit/b533be2965a8cac5911f0ea0a1fe2fa77601e19c))
* **deps:** update dependency ruff to v0.1.8 ([c39bec9](https://github.com/muhlba91/onyx-homeassistant-integration/commit/c39bec95bd047e6121df3f15b02457a43ba55d58))
* **deps:** update github/codeql-action action to v3 ([e57a75b](https://github.com/muhlba91/onyx-homeassistant-integration/commit/e57a75be5ff963cd09777c82c46635bb9985c428))
* **deps:** update google-github-actions/release-please-action action to v4 ([844bbac](https://github.com/muhlba91/onyx-homeassistant-integration/commit/844bbac22fd54e9ed04eea86e1f9e092b5b54de1))


### Code Refactoring

* refactor background events ([d13df42](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d13df429a11832fadf14210fef47902b8653a6dd))

## [7.0.0](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v6.0.1...v7.0.0) (2023-11-16)


### ⚠ BREAKING CHANGES

* weather sensors are untested due to lack of device

### Features

* implement support for weather sensors; related to [#72](https://github.com/muhlba91/onyx-homeassistant-integration/issues/72) ([0830d24](https://github.com/muhlba91/onyx-homeassistant-integration/commit/0830d247009eb414de85b7e6d380a5039b4d0eec))


### Bug Fixes

* add suggested decimal precision to weather sensors ([cf0d23c](https://github.com/muhlba91/onyx-homeassistant-integration/commit/cf0d23c5f63542d4bdeafca33e833293efc0e803))
* **ci:** fix snyk ([6b41652](https://github.com/muhlba91/onyx-homeassistant-integration/commit/6b4165276e6a487af19277b3c7c6a6f7e980affc))
* fix setup routine ([e214f47](https://github.com/muhlba91/onyx-homeassistant-integration/commit/e214f475674d7970ce400490ee3558d3fb238688))


### Miscellaneous Chores

* **deps:** update actions/checkout action to v4 ([9d28693](https://github.com/muhlba91/onyx-homeassistant-integration/commit/9d28693e483ba3241c7f7d2eb85ff4a8e9485d96))
* **deps:** update dependency aioresponses to v0.7.5 ([f988e53](https://github.com/muhlba91/onyx-homeassistant-integration/commit/f988e53e35015401282da10adaf7fdd38106c7d2))
* **deps:** update dependency black to v23.10.0 ([52e17de](https://github.com/muhlba91/onyx-homeassistant-integration/commit/52e17de59d1828674cfa5f9173f1457ba667e7ac))
* **deps:** update dependency black to v23.10.1 ([3cf3767](https://github.com/muhlba91/onyx-homeassistant-integration/commit/3cf3767e45cdaa9b31d59b113f9eda79a4d3bffb))
* **deps:** update dependency black to v23.11.0 ([49c22c1](https://github.com/muhlba91/onyx-homeassistant-integration/commit/49c22c1e162e35a4796149d50859a042096a82fb))
* **deps:** update dependency black to v23.9.0 ([21770ff](https://github.com/muhlba91/onyx-homeassistant-integration/commit/21770ff82ba002f33e4afb907675e2cfea9472cb))
* **deps:** update dependency black to v23.9.1 ([417335c](https://github.com/muhlba91/onyx-homeassistant-integration/commit/417335c4f1be3dc5cf41a8598fd3fee0c8d3de22))
* **deps:** update dependency coverage to v7.3.1 ([783d627](https://github.com/muhlba91/onyx-homeassistant-integration/commit/783d627b543a2f5d90ac0efb46b0f2c16bfd8aa3))
* **deps:** update dependency coverage to v7.3.2 ([3b15811](https://github.com/muhlba91/onyx-homeassistant-integration/commit/3b15811a28f006729c9e084cd7a3c090c60580c7))
* **deps:** update dependency homeassistant to v2023.10.0 ([747d9b7](https://github.com/muhlba91/onyx-homeassistant-integration/commit/747d9b7cde112094902b7660b48210b5bb2b2795))
* **deps:** update dependency homeassistant to v2023.11.0 ([21c2b58](https://github.com/muhlba91/onyx-homeassistant-integration/commit/21c2b58de931164f5edfe7e4ccf6cb4de213b005))
* **deps:** update dependency homeassistant to v2023.9.0 ([5e0bf16](https://github.com/muhlba91/onyx-homeassistant-integration/commit/5e0bf16f92c88f8553acc798c62b17ab1e18e3ec))
* **deps:** update dependency pre-commit to v3.4.0 ([76fb680](https://github.com/muhlba91/onyx-homeassistant-integration/commit/76fb680ae1be92a705858932d5515919c99db313))
* **deps:** update dependency pre-commit to v3.5.0 ([1a3295e](https://github.com/muhlba91/onyx-homeassistant-integration/commit/1a3295ec5988d0d2dac892dd54d72e65006e1cb8))
* **deps:** update dependency pytest to v7.4.1 ([7b5b77b](https://github.com/muhlba91/onyx-homeassistant-integration/commit/7b5b77b883f798fc71fed3f45157bfe7c6c95c64))
* **deps:** update dependency pytest to v7.4.2 ([78a2730](https://github.com/muhlba91/onyx-homeassistant-integration/commit/78a273098f58d54b3da5a547b70e1cb86a031a7f))
* **deps:** update dependency pytest to v7.4.3 ([dead328](https://github.com/muhlba91/onyx-homeassistant-integration/commit/dead328051b0401a10e9414454814a2a73fcd2c2))
* **deps:** update dependency pytest-asyncio to ^0.22.0 ([bac5f94](https://github.com/muhlba91/onyx-homeassistant-integration/commit/bac5f948903a7af92494510e758e8b11fac08eaf))
* **release:** prepare v7.0.0-beta.0 release ([f731ab0](https://github.com/muhlba91/onyx-homeassistant-integration/commit/f731ab0add26227961af5710ab1bb239db982caa))

## [6.0.1](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v6.0.0...v6.0.1) (2023-08-29)


### Miscellaneous Chores

* **ci:** fix release-please commit message ([21753f0](https://github.com/muhlba91/onyx-homeassistant-integration/commit/21753f03c4c255fd20008250acaaccecce1c2646))
* **deps:** update client to 7.1.1 ([8e16a76](https://github.com/muhlba91/onyx-homeassistant-integration/commit/8e16a76757e13b0922d26568da17c4b8c86813b9))
* **deps:** update dependency black to v23.7.0 ([5db15c1](https://github.com/muhlba91/onyx-homeassistant-integration/commit/5db15c11a1c60ca12f79fbe34efada1652747805))
* **deps:** update dependency coverage to v7.3.0 ([ecffee6](https://github.com/muhlba91/onyx-homeassistant-integration/commit/ecffee6d644e3eff117b9ac59cdff8bdd8c963d0))
* **deps:** update dependency homeassistant to v2023.6.1 ([37159dd](https://github.com/muhlba91/onyx-homeassistant-integration/commit/37159dde1204f13a211f801397d2db7996ca033f))
* **deps:** update dependency homeassistant to v2023.6.2 ([d261610](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d26161059b5f6a0dd2fb45a3cdf3d2952e8625ef))
* **deps:** update dependency homeassistant to v2023.6.3 ([d4d30b1](https://github.com/muhlba91/onyx-homeassistant-integration/commit/d4d30b1de38e55876896e428f370c0c214e9efcc))
* **deps:** update dependency homeassistant to v2023.7.0 ([3c162c1](https://github.com/muhlba91/onyx-homeassistant-integration/commit/3c162c1e4ca52af89adb87f27008f91ebb1e3a4c))
* **deps:** update dependency homeassistant to v2023.7.1 ([ef80b3a](https://github.com/muhlba91/onyx-homeassistant-integration/commit/ef80b3a3e5768b1384e242c5e330c2be250f300a))
* **deps:** update dependency homeassistant to v2023.7.2 ([3b1946f](https://github.com/muhlba91/onyx-homeassistant-integration/commit/3b1946ff3adbb5673f2de442f336ffaa1ff46def))
* **deps:** update dependency homeassistant to v2023.8.0 ([20fce5c](https://github.com/muhlba91/onyx-homeassistant-integration/commit/20fce5c85aac894cba0c6f6cde95a4337aa334e6))
* **deps:** update dependency pre-commit to v3.3.3 ([6fbe746](https://github.com/muhlba91/onyx-homeassistant-integration/commit/6fbe74690d16d2c9493411f8cf18dfe86807c5fc))
* **deps:** update dependency pytest to v7.3.2 ([bba3b0b](https://github.com/muhlba91/onyx-homeassistant-integration/commit/bba3b0bf8a2c73b589ef555b4d3969dc6d0e10aa))
* **deps:** update dependency pytest to v7.4.0 ([ecae10d](https://github.com/muhlba91/onyx-homeassistant-integration/commit/ecae10dc9e8fe29f73d14cbe0a3d30fed352d0e5))
* **deps:** update dependency pytest-asyncio to v0.21.1 ([91cc1b1](https://github.com/muhlba91/onyx-homeassistant-integration/commit/91cc1b107d00333df6adcd849699dddbeb50acc1))
* **release:** release 6.0.1-beta.0 [skip ci] [release] ([31bbda9](https://github.com/muhlba91/onyx-homeassistant-integration/commit/31bbda977a7b1549ee577718f066642d54a656fd))
* **release:** release 6.0.1-beta.1 [skip ci] [release] ([051403d](https://github.com/muhlba91/onyx-homeassistant-integration/commit/051403db602eb0ad1c96a4bb986d48e9f0e2329c))
* replace standard-version with release-please ([8bf87d7](https://github.com/muhlba91/onyx-homeassistant-integration/commit/8bf87d7428d9b969433f3164eb80f16c00e72dd2))

### [6.0.1-beta.1](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v6.0.1-beta.0...v6.0.1-beta.1) (2023-06-11)

### [6.0.1-beta.0](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v6.0.0...v6.0.1-beta.0) (2023-06-10)

## [6.0.0](https://github.com/muhlba91/onyx-homeassistant-integration/compare/v6.0.0-beta.0...v6.0.0) (2023-06-08)
