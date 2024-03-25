# Changelog

## [1.6.0](https://github.com/chichann/jav_study/compare/v1.5.6...v1.6.0) (2024-03-25)


### Features

* 🎸 支持馒头的api令牌访问 ([4b0099f](https://github.com/chichann/jav_study/commit/4b0099f7b0def37ac38dbdc10122429352bda85c))

### [1.5.6](https://github.com/chichann/jav_study/compare/v1.5.5...v1.5.6) (2024-03-23)


### Bug Fixes

* 🐛 适配馒头新接口 ([5284424](https://github.com/chichann/jav_study/commit/5284424f0cdce2f4a765b86530dbc36c752e1416))

### [1.5.5](https://github.com/chichann/jav_study/compare/v1.5.4...v1.5.5) (2023-10-04)


### Bug Fixes

* 优化依赖的引入 ([7861f6d](https://github.com/chichann/jav_study/commit/7861f6df9f3245796b54bd222d08928ea16a0cee))

### [1.5.4](https://github.com/chichann/jav_study/compare/v1.5.3...v1.5.4) (2023-10-04)


### Bug Fixes

* 解决BUS跳登录页面导致无法搜索的问题 ([8cd195b](https://github.com/chichann/jav_study/commit/8cd195b8c446b92a1d42c379ee2bab7f216b069b))

### [1.5.3](https://github.com/chichann/jav_study/compare/v1.5.2...v1.5.3) (2023-09-24)


### Bug Fixes

* 优化种子下载逻辑 ([edf12ba](https://github.com/chichann/jav_study/commit/edf12bae3799b352df4658a50a5f845a52500ee3))

### [1.5.2](https://github.com/chichann/jav_study/compare/v1.5.1...v1.5.2) (2023-09-07)


### Bug Fixes

* 修复init引入问题 ([889e2ee](https://github.com/chichann/jav_study/commit/889e2ee31d1b480e2d12f39073296c031e1d2b7f))

### [1.5.1](https://github.com/chichann/jav_study/compare/v1.5.0...v1.5.1) (2023-09-07)


### Bug Fixes

* 修复引用错误等bug ([1dc9353](https://github.com/chichann/jav_study/commit/1dc9353de269b1e141e063565f873a2d54a7e242))

## [1.5.0](https://github.com/chichann/jav_study/compare/v1.4.2...v1.5.0) (2023-09-07)


### Features

* 增加plex媒体库支持 ([85009f0](https://github.com/chichann/jav_study/commit/85009f068ddb772e2a3fd15790aefdf72c8c540f))


### Bug Fixes

* 修复图片地址链接 ([341529a](https://github.com/chichann/jav_study/commit/341529a137d1892bba61c595c9064f74a416b810))
* 修复馒头请求种子错误 ([63f3168](https://github.com/chichann/jav_study/commit/63f31689518976c68a37bf7262d5e828e5222562))

### [1.4.2](https://github.com/chichann/jav_study/compare/v1.4.1...v1.4.2) (2023-04-02)


### Bug Fixes

* 修复订阅演员时页面解析可能出错的问题 ([2015971](https://github.com/chichann/jav_study/commit/20159713befcd9216d2d165f8d8e1e1b0f286288))

### [1.4.1](https://github.com/chichann/jav_study/compare/v1.4.0...v1.4.1) (2023-03-28)


### Bug Fixes

* 推送可选无图模式 ([ee17632](https://github.com/chichann/jav_study/commit/ee17632c32a3ba874ef3b19c01971daf23a54005))
* 远程搜索无结果不再强制等待 ([af38954](https://github.com/chichann/jav_study/commit/af38954906f428f4a0dae30d4cbd981b1d2830e2))

## [1.4.0](https://github.com/chichann/jav_study/compare/v1.3.0...v1.4.0) (2023-03-14)


### Features

* 提交下载成功时发送系统通知 ([d846faf](https://github.com/chichann/jav_study/commit/d846faf75b8f3785dff01a4d797f901b1a1758a4))


### Bug Fixes

* 优化馒头限流时的日志提示 ([738ae7c](https://github.com/chichann/jav_study/commit/738ae7c2f14460363d2074558afb6c460b80367b))

## [1.3.0](https://github.com/chichann/jav_study/compare/v1.2.23...v1.3.0) (2023-03-09)


### Features

* 增加安装及更新MDC-NG功能 ([c471513](https://github.com/chichann/jav_study/commit/c471513b3bf66924798e0241acb7bd802cda3551))

### [1.2.23](https://github.com/chichann/jav_study/compare/v1.2.22...v1.2.23) (2023-03-09)


### Bug Fixes

* 修复馒头长时间限流可能导致下载种子无限循环的问题 ([a6247c1](https://github.com/chichann/jav_study/commit/a6247c1125bb5b940915216292746e17057110dd))

### [1.2.22](https://github.com/chichann/jav_study/compare/v1.2.21...v1.2.22) (2023-03-08)


### Bug Fixes

* 优化种子权重算法，放宽做种人数和下载完成人数的条件 ([e068860](https://github.com/chichann/jav_study/commit/e0688606d37544d8a422f14d74be52c7e287e5b7))
* 若所有种子最大权重仅为0时，选择做种人数最多的种子提交下载 ([e068860](https://github.com/chichann/jav_study/commit/e0688606d37544d8a422f14d74be52c7e287e5b7))

### [1.2.21](https://github.com/chichann/jav_study/compare/v1.2.20...v1.2.21) (2023-03-07)


### Bug Fixes

* 从未下载列表里删除的榜单影片同步时不会再添加进去 ([d0228d8](https://github.com/chichann/jav_study/commit/d0228d86163b2551412de18b35cb0e39728a96e6))

### [1.2.20](https://github.com/chichann/jav_study/compare/v1.2.19...v1.2.20) (2023-03-05)


### Bug Fixes

* 优化老师无头像时的处理 ([7889624](https://github.com/chichann/jav_study/commit/78896242b2e9c01395d5f9f709fc97068697dc08))
* 优化选种的详情日志打印 ([053992a](https://github.com/chichann/jav_study/commit/053992aee5e27b8d6f47194a93366509614ac986))
* 修复同步TOP20时的库存判断逻辑问题 ([0a3bb56](https://github.com/chichann/jav_study/commit/0a3bb5674efa2e6afac3a8fded75fa5f7561a431))

### [1.2.19](https://github.com/chichann/jav_study/compare/v1.2.18...v1.2.19) (2023-03-01)


### Bug Fixes

* 影片数据增加演员信息 ([38be6f4](https://github.com/chichann/jav_study/commit/38be6f47e86e062601cda0ebd9d5bf8ec030fd1b))

### [1.2.18](https://github.com/chichann/jav_study/compare/v1.2.17...v1.2.18) (2023-02-28)


### Bug Fixes

* 增加只下中文全局选项，选种时排除无中文资源 ([3c74c50](https://github.com/chichann/jav_study/commit/3c74c507022a057fbaecedcf92114f215bdf8a2d))

### [1.2.17](https://github.com/chichann/jav_study/compare/v1.2.16...v1.2.17) (2023-02-28)


### Bug Fixes

* 优化头像获取报错；放宽演员搜索限制，搜索结果超过一个时自动取第一个 ([0ce8d9b](https://github.com/chichann/jav_study/commit/0ce8d9b156cd9906b4ada03e59edf27466ee8b0d))
* 优化种子下载报错 ([14e3b63](https://github.com/chichann/jav_study/commit/14e3b635b1a4c96e64d9e6a9a0745e44fdd10bc3))

### [1.2.16](https://github.com/chichann/jav_study/compare/v1.2.15...v1.2.16) (2023-02-27)


### Bug Fixes

* 增加一键更新插件任务 ([4fa1183](https://github.com/chichann/jav_study/commit/4fa118368c7bfe9fe571450adfdbc08ea5222fca))

### [1.2.15](https://github.com/chichann/jav_study/compare/v1.2.14...v1.2.15) (2023-02-27)


### Bug Fixes

* 修正tag ([3bb3099](https://github.com/chichann/jav_study/commit/3bb309973352855effe884ba91b6d76694070417))

## 1.2.14 (2023-02-27)


### Bug Fixes

* 增加bus备用站轮询 ([ab21044](https://github.com/chichann/jav_study/commit/ab2104454e97ef5b685ee9dbcb930d82eecbf78d))
