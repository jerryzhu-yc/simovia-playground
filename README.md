# 宇树 G1 收拾毛毯：PICO 遥操作 + LeRobot 数据链路

> Simovia Playground 分支 `demo/g1-cloth`。PICO 头显浏览器直连控制器（无需装 APP），手柄经操作空间控制（OSC）遥操作 G1 + 2F85 夹爪把桌上毛毯抓起放进盒子；A 键一键录制 LeRobot 数据集，随后可做域随机化增强、动作回放与策略评测——完整「遥操作采集 → 数据增强 → 训练 → 评测」链路演示。

## 看点

- **VR 遥操作**：手柄位姿 → OSC 末端速度 → G1 上半身关节目标；WebXR 页面（`g1_cloth_webxr.html`）即开即用。
- **LeRobot 数据集**：多路相机（第三人称 + 腕部）+ 关节状态/动作逐帧落盘 v2.1，退出自动升级 v3.0。
- **数据增强**：`g1_cloth_augment.py` 对采集集做域随机化增强。
- **策略评测**：`g1_cloth_policy_eval.py` 把训练好的策略放回仿真闭环评测。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/g1_cloth_teleop.yaml` | 遥操作采集世界（G1 + 2F85 + 毛毯 + 盒子） |
| `controllers/g1_cloth_teleop.py` | 遥操作 + 录制控制器 |
| `controllers/g1_cloth_augment.py` | 数据增强脚本 |
| `controllers/g1_cloth_policy_eval.py` | 策略评测世界与控制器 |
| `controllers/g1_cloth_webxr.html` | PICO 浏览器 WebXR 前端 |

## 复现流程

```bash
git checkout demo/g1-cloth
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

# 1) 采集（需要 PICO 与主机同网段；具体配网/证书步骤见主仓库 README「PICO 遥操作」章节）
python -m simovia run worlds/g1_cloth_teleop.yaml --record episodes/g1_demo
#    PICO 浏览器打开 WebXR 页面 → 手柄遥操作 → A 键录制/结束单集

# 2) 增强 / 回放 / 评测
python controllers/g1_cloth_augment.py
python -m simovia run worlds/g1_cloth_policy_eval.yaml

# 3) GUI 观察多路相机
python -m simovia gui
```

## 常见问题

- **PICO 连不上**：控制器监听端口需与头显同网段可达；主仓库 README 有证书信任与防火墙排障清单。
- **数据集升 v3.0 慢**：仅在控制器退出时执行一次，属预期行为。
