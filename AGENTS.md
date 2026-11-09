# OHT 离线包：维护入口

本目录是交付安装包，包含三个大型归档和安装辅助程序。它与已安装的
`/home/yiwei/OHT_offline` 是两个目录；修改其中一处不会自动同步另一处。

接手相机、迁移或安装问题时，先读
[2026-11-09 相机移植修复记录](docs/CAMERA_PORTABILITY_FIX_20261109.md)。
其中列出了根因、实际修改、运行时补丁、备份、验证和待处理事项。

- `install.sh` 校验、解压后调用 `tools/relocate.py`；新安装的 ZED 修复由迁移脚本注入，三个归档没有重新打包。
- `tools/install_usb_rules.sh` 已补充 `plugdev` 组。规则和用户组生效是两个不同步骤，现有进程不会自动获得新组。
- `inventory/verification.json` 是 2026-11-06 原始打包验证记录；本次目标机相机预览证据在 `inventory/target_camera_preview_20261109.json`。三路预览通过不代表机器人、模型推理或正式采集通过。
- 已安装程序的实际目录和解释器从其 `installation.json` 读取；不要依赖当前 Conda 环境。
- 不要对已有安装重新运行 `relocate.py` 来应用单项修复：它还会创建数据链接并拒绝已有链接，不是升级脚本。
- 相机日志在 `installation.json` 的 `original` 目录下的 `ui_runtime/cameras/`；`current.json` 指向当前一轮，历史失败日志不能作为当前状态。
- 修改交付文件后更新 `SHA256SUMS`，新增交付文件也要加入；不要为了更新几个小文件重新计算大型归档的哈希。

进一步测试应记录新时间和实际结果。不要把旧报告、固定 PID 或旧的 `ready: true` 当作当前机器状态。
