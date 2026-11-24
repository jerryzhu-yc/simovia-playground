# 三机协同维修接力（Go2 × G1 × UR5e）

> Simovia Playground 分支 `demo/maintenance-relay`。UR5e 抓取维修模块装到 Go2 运输架，Go2 配送到维修工位，G1 取件放入导向槽并按下复位按钮——三台机器人各自独立控制器、统一时钟调度，交接全靠接触与摩擦完成。

## 看点

- **多机器人同场**：三台机器人各配独立控制器进程（Webots 风格），ZMQ 栅栏同步共享一个物理世界。
- **无通信交接**：Go2 运输架 ↔ G1 取件全靠几何对位与接触摩擦，不靠魔法传值。
- **统一调度**：各控制器按仿真时钟分相位推进，`task.success` 校验最终按钮按下。

## 文件

| 文件 | 说明 |
|---|---|
| `demo/maintenance_relay/` | demo 包：三个控制器与工位夹具（碰撞安全设计） |
| `worlds/` | 世界文件以 demo 包内说明为准 |

## 复现流程

```bash
git checkout demo/maintenance-relay
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

# 入口以 demo/maintenance_relay/ 内 README 为准（多控制器世界）
python -m simovia gui
python -m pytest tests/ -q
```

## 常见问题

- **接力掉件**：多机接触交接对 timestep 敏感，保持世界默认 `timestep`/`integrator` 组合。
- **某台机器人不动**：多控制器进程模型下，`python -m simovia run` 的统计会列出每台控制器崩溃/超时明细，按名单排查。
