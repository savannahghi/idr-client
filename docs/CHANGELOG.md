## [0.3.0](https://github.com/savannahghi/idr-client/compare/v0.2.0...v0.3.0) (2022-10-14)


### Features

* **lib:** implement concurrent executor task ([#55](https://github.com/savannahghi/idr-client/issues/55)) ([2f6020e](https://github.com/savannahghi/idr-client/commit/2f6020edf764fe4af0851d147d8423202ac5de70))
* **lib:** implement the retry functionality ([#57](https://github.com/savannahghi/idr-client/issues/57)) ([bc1bf4d](https://github.com/savannahghi/idr-client/commit/bc1bf4d55f688d2fe647bafddf76f272c8736f2c))


### Bug Fixes

* **http:** extract metadata fetching ([#54](https://github.com/savannahghi/idr-client/issues/54)) ([8c62944](https://github.com/savannahghi/idr-client/commit/8c62944b2edc69e9d711a4aa826c9d7238aeea6c))
* **http:** make the HTTP transport threadsafe ([#56](https://github.com/savannahghi/idr-client/issues/56)) ([b1a56a9](https://github.com/savannahghi/idr-client/commit/b1a56a91002feeccb3c25aa88fa4308a53262771))
* **ci:** release CI ([#64](https://github.com/savannahghi/idr-client/issues/64)) ([d59ec0e](https://github.com/savannahghi/idr-client/commit/d59ec0e23a7d37a6d81536dd9b78970b04056b33))


### Dependency Updates

* **deps:** update project dependencies ([#58](https://github.com/savannahghi/idr-client/issues/58)) ([8ddd4ab](https://github.com/savannahghi/idr-client/commit/8ddd4abbe0b25d00500d07031cde2519cba01d9f))


### Refactors

* **http:** encapsulate HTTPTransport ([#59](https://github.com/savannahghi/idr-client/issues/59)) ([38c3fd1](https://github.com/savannahghi/idr-client/commit/38c3fd1d92f488332f2f1aaae8bd43e0ba74dc3f))
* **sql_data:** encapsulate sql_data implementation ([#60](https://github.com/savannahghi/idr-client/issues/60)) ([30f2741](https://github.com/savannahghi/idr-client/commit/30f274187fe996862208fb2a2184c7fca68c2f24))
* **build:** migrate to python3.9 ([#62](https://github.com/savannahghi/idr-client/issues/62)) ([436152a](https://github.com/savannahghi/idr-client/commit/436152adb6fec01109af4479d07ab5a5e04a9369))
* **use_cases:** move the retry functionality to use cases ([#61](https://github.com/savannahghi/idr-client/issues/61)) ([fa2d44a](https://github.com/savannahghi/idr-client/commit/fa2d44a24c24c2ddb42b5dd7cfd98edd5a53bb28)), closes [#59](https://github.com/savannahghi/idr-client/issues/59) [#60](https://github.com/savannahghi/idr-client/issues/60)
* **use_cases:** move upload completion to separate task ([#50](https://github.com/savannahghi/idr-client/issues/50)) ([5c5919e](https://github.com/savannahghi/idr-client/commit/5c5919e82f036f12a51147ea56dc3f6357b4a21b))
* **use_cases:** refactor main pipeline use_cases ([#51](https://github.com/savannahghi/idr-client/issues/51)) ([2cc16bd](https://github.com/savannahghi/idr-client/commit/2cc16bd10d2fc73d0cb77a4e912ad345d8711d8c))

## [0.2.0](https://github.com/savannahghi/idr-client/compare/v0.1.0...v0.2.0) (2022-08-18)


### Features

* **core:** add data upload api on transport interface ([#34](https://github.com/savannahghi/idr-client/issues/34)) ([43de98f](https://github.com/savannahghi/idr-client/commit/43de98fd8d5019863102fcadeb9ca1767a0b67c0))
* **core:** add data upload interfaces ([#32](https://github.com/savannahghi/idr-client/issues/32)) ([677fe25](https://github.com/savannahghi/idr-client/commit/677fe2544d693582c9a90324256bf09b92260dd1))
* **core:** add transport api for marking uploads as completed ([#37](https://github.com/savannahghi/idr-client/issues/37)) ([9ce91b1](https://github.com/savannahghi/idr-client/commit/9ce91b1775846254b7688c2567f772731f98cfee))
* **core:** implement data upload api on transport implementations ([#35](https://github.com/savannahghi/idr-client/issues/35)) ([4a67b74](https://github.com/savannahghi/idr-client/commit/4a67b74998c5dd89f1eebaaa33205e52eab900d2))
* **core:** implement data upload interfaces ([#33](https://github.com/savannahghi/idr-client/issues/33)) ([843bf91](https://github.com/savannahghi/idr-client/commit/843bf91ffbf4359dfbaa51cdaf6a4d77594c805f)), closes [#32](https://github.com/savannahghi/idr-client/issues/32)
* **core:** implement transport api for marking uploads as completed ([#38](https://github.com/savannahghi/idr-client/issues/38)) ([b61eff5](https://github.com/savannahghi/idr-client/commit/b61eff50c20655c61663cbd1029d610572813429))
* **usecases:** mark completed uploads ([#39](https://github.com/savannahghi/idr-client/issues/39)) ([323fb75](https://github.com/savannahghi/idr-client/commit/323fb75844c30ef0ca30e33dee034e69dd6faebd))
* **usecases:** wire up data upload functionality ([#36](https://github.com/savannahghi/idr-client/issues/36)) ([ebbd2ae](https://github.com/savannahghi/idr-client/commit/ebbd2ae278c73b447290d00452e35af377906688))


### Bug Fixes

* **ci:** configure git user details for release ci ([#46](https://github.com/savannahghi/idr-client/issues/46)) ([d394810](https://github.com/savannahghi/idr-client/commit/d39481056eb965cab137c5487dd3c60b816ea7f0))
* **ci:** mark semantic-release jobs as non-dry runs ([#43](https://github.com/savannahghi/idr-client/issues/43)) ([1f409da](https://github.com/savannahghi/idr-client/commit/1f409da137aa9043e53cad4f2aeff6bf970243d0))


### Refactors

* **domain:** domain models to simplify the codebase ([#29](https://github.com/savannahghi/idr-client/issues/29)) ([e5e8e5b](https://github.com/savannahghi/idr-client/commit/e5e8e5b6855fd08c9a3b7f71bade5ee109dcfac8))
* **usecases:** simplify the main pipeline by utilizing earlier refactors ([#30](https://github.com/savannahghi/idr-client/issues/30)) ([02712ab](https://github.com/savannahghi/idr-client/commit/02712abdd41bd535a4f327ee458b8a716718c820))
* **ci:** update release ci ([#41](https://github.com/savannahghi/idr-client/issues/41)) ([e3862b6](https://github.com/savannahghi/idr-client/commit/e3862b6e5155ff61d85187d21e21cbdede80d26e))
