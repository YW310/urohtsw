# 相机移植修复记录：2026-11-09

本文供后续维护者和 Codex 接手使用，记录已经实施的修改，不代表机器当前仍处于相同运行状态。日期以 Asia/Shanghai 为准。

## 结果和证据

在 `/home/yiwei/OHT_offline` 安装副本上验证：两台 RealSense D405 和一台 ZED Mini 均产生实时预览，APP 的 `/api/status` 和 `/api/frames` 均返回 HTTP 200。

机器可读证据见 [target_camera_preview_20261109.json](../inventory/target_camera_preview_20261109.json)。
[verification.json](../inventory/verification.json) 保留的是 2026-11-06 原始打包验证，不能据其中的“未开启相机”推断本次没有验证预览，也不能把本次预览通过解释成全部硬件通过。

| 相机 | SDK 序列号 | 本次结果 | USB 链路 |
| --- | --- | --- | --- |
| camera_0 | 260322272556 | 实时 JPEG 可取、相机检查通过 | RealSense USB 3.2 |
| camera_1 | 260322279549 | 实时 JPEG 可取、相机检查通过 | RealSense USB 2.1，仍需改善 |
| camera_2 | 15891605 | 实时 JPEG 可取、相机检查通过 | ZED 5000 Mbps |

本次没有启动机器人连接、机器人运动或正式 episode 采集；没有验证模型 GPU 预热、保存完整性、标定精度或长时间稳定性。

## 现象与根因

### 1. 权限规则和用户组没有完全生效

起初系统能在 USB 树中看到 ZED，但 ZED SDK 返回空设备列表。当前用户缺少 USB 写入、HID 访问权限；目标机也没有安装交付包的 ZED udev 规则。

原来的 USB 安装脚本只添加 `dialout,video`，而 `udev/99-zed-mini.rules` 使用的是 `plugdev` 组。因此仅运行旧脚本还不完整。

用户安装规则、添加组后，旧 APP 进程仍继承旧组，设备节点也尚未重新应用规则。重启后确认进程已有新组，ZED USB 节点可读写。**账户组列表、运行进程的组、设备节点权限要分别检查**。

### 2. ZED 原生 SDK 仍使用系统标定目录

权限修复后，SDK 打开 ZED 时仍尝试读取 `/usr/local/zed/settings/`。该目录在目标机不存在，而正确的出厂标定文件已经包含在：

```text
<installation_root>/usr/local/zed/settings/SN15891605.conf
```

迁移 Python 路径、设置 `LD_LIBRARY_PATH` 不会自动改变原生 SDK 的标定搜索目录。找不到文件后，SDK 启动 shell/curl 下载标定，日志出现：

```text
No calibration file found for SN 15891605. Downloading...
```

这些下载子进程继承了 `/dev/video0` 句柄。相机 worker 超时退出后，子进程仍存在并占着设备，导致后续启动反复报：

```text
ZED 15891605 not available; SDK serials: []
```

因此同一个“SDK 列表为空”错误，在不同阶段既可能与权限有关，也可能与设备占用有关，不能一直重复添加用户组。

### 3. 标定目录必须保留结尾斜杠

本次使用 ZED SDK 4.2.5。`sl.InitParameters.optional_settings_path` 可以指定出厂标定目录；本次实测不带结尾 `/` 时仍触发下载，补上 `/` 后正常读取包内文件。

正确形式是在 `device.open(params)` 之前设置：

```python
params.optional_settings_path = "/实际安装目录/usr/local/zed/settings/"
```

这是出厂标定目录，不是 OpenCV 标定文件。不要用 `optional_opencv_calibration_file` 替代它，也不要复制其他序列号的标定来绕过错误。

## 实际修改了什么

| 位置 | 修改及作用 |
| --- | --- |
| [tools/relocate.py](../tools/relocate.py) | 遍历解压后的 `zed_camera_worker.py`，在 `params.coordinate_units = sl.UNIT.METER` 后插入指向包内 `usr/local/zed/settings/` 的 `params.optional_settings_path`。使用目标安装根目录并保留结尾斜杠。 |
| [tools/install_usb_rules.sh](../tools/install_usb_rules.sh) | 将添加用户组从 `dialout,video` 改为 `dialout,video,plugdev`。 |
| [inventory/package.json](../inventory/package.json) | 新增更新标识 `20261109-zed-offline-settings-usb-groups`。 |
| [inventory/target_camera_preview_20261109.json](../inventory/target_camera_preview_20261109.json) | 记录本次目标机预览、测试和验证范围。 |
| 交付目录的 `SHA256SUMS` | 更新交付文件哈希，登记新增报告及维护文档；安装器不会将此清单复制到运行目录。 |

迁移注入有两个约束：源文件已有 `params.optional_settings_path` 时跳过；找不到预期插入位置时明确失败，不假装修复成功。它不会检查已存在的赋值是否正确，后续维护者仍需确认路径和结尾斜杠。

**三个 tar.gz 保持原样，没有重新打包。** 新安装按 `install.sh` → 解压 → 复制 tools → `relocate.py` 的顺序自动注入修复；单独解压归档或仅复制新版 tools 到旧安装，不会自动修复 worker。

### 已安装副本的改动

从 `/home/yiwei/OHT_offline/installation.json` 读取 `app`、`original`、`manager`，三处目录下的 `zed_camera_worker.py` 均补充了上述赋值。三处分别是：

```text
home/samsung/codex_work/gello_shadow_session_20260921T061545_594387Z/
  oht_replay_unified_v1_20261030/
  teleop_capture_v5_hex_insert/
  dagger_capture_v1_20261022/
```

同时同步了安装副本的 `tools/relocate.py` 和 `tools/install_usb_rules.sh`。

上述五个被修改文件旁均保留原文件，后缀为 `.camera-fix-20261109.bak`。交付目录中的工具、安装副本中的工具，以及安装后的 worker 是不同文件，后续变更时应明确更新范围。

本次还终止了已确认孤立、正在下载本台 ZED 标定且持有视频句柄的 shell/curl 子进程。这是一次运行时清理，**没有新增自动清理逻辑**。不要沿用旧 PID，也不要用宽泛的 `pkill curl` 清理其他进程。

系统权限配置由用户执行 USB 脚本及添加 `plugdev`，随后重启生效。`install.sh` 本身仍不会自动执行需要管理员权限的 USB 配置。

## 如何复查与验证

### 先区分交付包和安装副本

```text
/home/yiwei/OHT_offline_package   交付目录，当前工作区
/home/yiwei/OHT_offline           已安装的运行目录
/home/yiwei/OHT_data              本次安装使用的数据目录
```

其他机器的路径可能不同，以目标安装的 `installation.json` 为准。启动脚本会选择包内解释器，不依赖终端激活的 `isaaclab_oht` Conda 环境。

### 日志与状态入口

实际相机服务运行在 `installation.json` 的 `original` 目录下，而不只是 `app` 目录：

```text
<original>/ui_runtime/cameras/service.log
<original>/ui_runtime/cameras/current.json
<current.json 中 directory>/status.json
<current.json 中 directory>/devices.json
<current.json 中 directory>/camera_2_console.log
```

`service.log` 累积了多轮旧错误，排查时先用 `current.json` 定位最新一轮，再检查状态更新时间。`start_cameras.sh` 的 “Camera startup requested” 只表示请求已提交；必须确认新鲜的 `ready: true`、无错误、三路帧时间持续更新。

RealSense 的 sysfs USB serial 可能对应 `asic_serial_number`，与 SDK 的 `serial_number` 不同。本次的 `255323070312` 和 `260322272556` 就分别是同一台设备的这两种标识；不要据此误改配置。

### 启动与只读检查

```bash
bash "$HOME/OHT_offline/start_oht.sh" &&
bash "$HOME/OHT_offline/start_cameras.sh"

curl --noproxy '*' -sS http://127.0.0.1:8779/api/status
```

APP 地址为 `http://127.0.0.1:8779`。`/api/status` 的 `checks.camera_0/1/2` 应为 `true`；`/api/frames` 的三路 `live` 应为 `true` 且 `jpeg` 非空。接口中可能包含较大的 JPEG 数据，不宜把完整响应贴入日志或聊天。

未连接机器人时，顶层 `ready` 和机器人检查可以为 `false`，这不等于相机预览失败。本次 APP 为 `phase: idle`，三路相机检查通过，接口显示“相机常驻预览 · 尚未保存”。

### 已完成的测试

- 新安装临时 fixture：三个 worker 都得到含结尾斜杠的标定路径；包含空格和引号的安装路径可解析；根启动脚本保持原样；数据链接位置正确。
- `bash -n tools/install_usb_rules.sh` 通过。
- 已安装 APP 目录内运行 `test_zed_camera`，18 项测试通过。这些是模拟集成测试，不能单独证明真实相机出帧。
- 随后实际启动相机，确认服务 `ready: true`、三路新鲜预览帧，以及两个 APP 接口 HTTP 200、三路实时 JPEG 可用。

重跑模拟测试时，进入实际 `app` 目录并使用 `installation.json` 的 `python` 解释器：

```bash
source "$HOME/OHT_offline/env.sh"
# 将两个路径替换为 installation.json 的 app 与 python 完整路径
cd /实际/app/目录
/实际/python/解释器 -B -m unittest -q test_zed_camera
```

### 复发时的排查顺序

1. 核对最新状态和具体错误，不把启动请求打印当成功。
2. 核对 SDK 序列号、USB 链路速度，以及账户组、进程组、实际设备权限。
3. 核对三份 worker 的标定路径、结尾 `/`、对应 `SN<序列号>.conf` 的存在和可读性。
4. 若 SDK 列表仍为空，检查视频设备占用及进程父子关系；仅处理已确认残留的相机下载进程。
5. 在空闲状态恢复相机服务，验证新鲜帧和 APP 接口，记录实际结果。

## 维护边界与仍待处理事项

- 不要重新运行 `relocate.py` 修补已有安装。该函数还会创建 episode 链接，并明确拒绝已有链接，不能作为幂等升级命令。旧安装应备份后定点修补，或使用全新安装目录。
- 不要为了修复这个问题重打三个大型归档。保留安装后注入机制，修改交付文件时同步 `SHA256SUMS`。
- 回滚已安装 worker 可使用相邻 `.camera-fix-20261109.bak`，应在相机不被采集任务使用时操作。恢复原文件也会恢复本次修复前的问题，且仍需处理设备占用。
- `camera_1` 仍协商为 USB 2.1，本次能够预览，但没有因此证明高负载采集稳定；后续应检查 USB 3 接口、线缆和 Hub。
- `inventory/package.json` 的 `target_hardware_verified: false` 保留：本次预览通过不足以把整个机器人系统标为已验证。
- 早前文档检查发现的独立问题尚未在本次修复：手册快速启动示例的命令未全部用 `&&` 串联；升级说明缺少旧服务退出步骤。不要将它们视为已完成修改。
