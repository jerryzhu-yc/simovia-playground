# Go2 对角小跑 sim2sim：原生 MuJoCo vs Simovia

> Simovia Playground 分支 `demo/go2-sim2sim`。同一个 Unitree Go2 模型、同一份 CPG 对角小跑控制律：左半用 **MuJoCo 原生 API** 直接步进，右半跑在 **Simovia 平台**里。目标域只改 4 项物理参数，两端同相机、同出生位姿、同时间轴做 4 秒并排对比。

## 看点

- **控制律只有一份**：`simovia/sim2sim/go2_trot.py`，纯 numpy，不 import mujoco 也不 import simovia。力矩执行器用 PD 跟踪 `q*(t) = home + amp·sin(2πf·t + 相位 + 膝滞后)`，对角腿反相。
- **名字驱动而不是 id**：控制律里 12 个执行器按固定名字顺序排列，目标端启动时校验 `robot.actuators`，首帧再校验观测里的 `joint_names`（MuJoCo 模型里是 `FL_hip_joint` 这种带 `_joint` 后缀的名字），不一致直接报错退出；全程不碰 MuJoCo 内部 id。
- **构造顺序对齐**：两端都是「空 spec → 地面/相机 → frame 平移 attach 机器人」。geom 顺序会改变接触求解顺序，四足是混沌系统，顺序不一致时同一控制律能跑出完全不同的轨迹——那样对比的就不是引擎差异了。
- **结果可核对**：同一套物理配置下，Simovia 4 秒终点 `(+2.816, −1.772)`，原生 MuJoCo `(+2.80, −1.76)`，**差约 1.6 cm**，说明契约与物理配置是真对齐的。
- **目标域只改物理**：控制周期 62.5→50 Hz、积分器 `implicitfast`→`implicit`、`impratio 100`→`20`、地面摩擦 `0.8`→`0.6`、重力 `−9.81`→`−9.6`，4 秒走 3.35 m（基线 2.80 m），步频与姿态肉眼可辨。
- **两个软件的画面本来就不一样**：MuJoCo 侧是它自带的灰地面与黑背景，Simovia 侧是天空盒 + 网格地面，对比视频里一眼能看出哪半是哪个软件。

## 环境要求

| 组件 | 要求 | 说明 |
|---|---|---|
| 仿真侧 | Python 3.11+（推荐 3.12）+ `requirements-core.txt` | `mujoco~=4.0`（源端用 `MjSpec` 程序化搭场景，需要 4.0+） |
| 源端单独跑 | 只要 `mujoco` + `numpy` | 不想装整套平台时 `pip install "mujoco~=4.0" numpy` 即可 |
| 录视频 | `ffmpeg`（在 PATH 里） | 源端走 ffmpeg rawvideo 管道；Simovia 侧录制 PNG 帧后再编码 |
| 渲染 | 有桌面直接开 viewer；无显示时 `MUJOCO_GL=egl` | `--video` / Simovia 录像都是离屏渲染 |
| 硬件 | CPU 即可 | 无 GPU、无训练权重、无外部模型下载 |

## 文件

| 文件 | 说明 |
|---|---|
| `simovia/sim2sim/go2_trot.py` | **唯一控制律**：Go2 对角小跑 CPG（参数、名字常量、`desired()`/`torques()`） |
| `simovia/sim2sim/__init__.py` | 包说明：不 import 任何引擎，参数按名字/固定顺序导出 |
| `controllers/go2_trot_sim2sim.py` | 目标端控制器：在 Simovia 内核里跑，按名字校验后每 tick 下发 12 个力矩 |
| `worlds/go2_trot_demo.yaml` | 基线世界，等价于模型库 `zoo.generate('unitree_go2', demo=True)` 的生成物 |
| `worlds/go2_trot_sim2sim.yaml` | sim2sim 目标域世界，只改物理参数 |
| `examples/sim2sim/mujoco_go2_trot.py` | 源端 runner：MuJoCo `MjSpec` 搭场景 + 原生 `mj_step`，支持 `--viewer` / `--video` / 轨迹日志 |
| `site/public/assets/demos/go2_sim2sim.mp4` | 并排对比视频（2560×1044，4.0 s，50 fps） |

## 复现流程

### 1) 环境

```bash
git checkout demo/go2-sim2sim
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements-core.txt
python -m simovia doctor      # 依赖 / 模型资产 / 离屏渲染 / 样例世界编译
```

### 2) 源端：直接跑 MuJoCo

```bash
# 打开 MuJoCo 自带 viewer，实时 62.5Hz；不加 --ticks 就一直走，Ctrl+C 或关窗退出
python examples/sim2sim/mujoco_go2_trot.py --viewer

# 只跑 4 秒并打印轨迹
python examples/sim2sim/mujoco_go2_trot.py --ticks 250 --log-every 50

# 录 mp4（离屏渲染；--stride 1 = 每 tick 一帧 = 62.5fps）
MUJOCO_GL=egl python examples/sim2sim/mujoco_go2_trot.py \
    --ticks 250 --video /tmp/go2_mujoco.mp4 --stride 1
```

外套壳打开后默认锁在 `showcase` 机位（与对比视频一致），按 Esc 可切自由视角。

### 3) 目标端：跑在 Simovia 里

```bash
python -m simovia run worlds/go2_trot_demo.yaml        # 基线：等价 zoo demo
python -m simovia run worlds/go2_trot_sim2sim.yaml     # sim2sim 目标域

# 或者 GUI：文件 → 打开世界 → 选上面的 yaml，相机下拉选 showcase
python -m simovia gui                                  # F5 运行 / F7 单步 / F8 重置 / F6 停止
```

### 4) 自己录一份对比视频（可选）

```bash
# 源端 62.5fps
MUJOCO_GL=egl python examples/sim2sim/mujoco_go2_trot.py \
    --ticks 250 --video /tmp/go2_src.mp4 --stride 1 --width 1280 --height 960

# 目标端 50fps PNG 帧
MUJOCO_GL=egl python -m simovia run worlds/go2_trot_sim2sim.yaml \
    --record /tmp/go2_tgt --record-images --record-camera showcase \
    --record-image-stride 1 --record-width 1280 --record-height 960
ffmpeg -y -framerate 50 -i /tmp/go2_tgt/frames/frame_%06d.png \
    -c:v libx264 -crf 20 -pix_fmt yuv420p /tmp/go2_tgt.mp4

# 统一到 50fps 后并排（标签/时间码按需改 drawtext）
ffmpeg -y -i /tmp/go2_src.mp4 -i /tmp/go2_tgt.mp4 -filter_complex \
  "[0:v]fps=50,scale=1280:960[l];[1:v]fps=50,scale=1280:960[r];[l][r]hstack=inputs=2[out]" \
  -map "[out]" -c:v libx264 -crf 18 -pix_fmt yuv420p /tmp/go2_compare.mp4
```

时间码来自 `drawtext=text='%{pts\:hms}'`，两边都用 `pts` 而不是各自的 tick 计数，所以并排后严格同一时间轴。

## 参数速查

**目标域与基线的差异（全部是物理，轨迹差异的唯一来源）**

| 参数 | 基线 `go2_trot_demo` | 目标域 `go2_trot_sim2sim` |
|---|---|---|
| `timestep` × `ctrl_period` | 0.002 × 8 = 0.016 s（62.5 Hz） | 0.0025 × 8 = 0.020 s（50 Hz） |
| `integrator` | `implicitfast` | `implicit` |
| `impratio` | 100 | 20 |
| `gravity` | `[0, 0, -9.81]` | `[0, 0, -9.6]` |
| 地面摩擦 | 0.8 | 0.6 |
| 相机 `showcase` / 出生位姿 / 任务时长 | `pos [3.289, 3.618, 2.315]`、`quat [0.151214, 0.098413, 0.536518, 0.824377]`、`fovy 50`、`pos [0,0,0.45]`、4 s | 完全一致 |

**控制律参数（`simovia/sim2sim/go2_trot.py`，与 zoo demo 原样同参）**

| 项 | 值 |
|---|---|
| 步频 `FREQ` / 站稳 `SETTLE` / 渐变 `RAMP` | 2.4 Hz / 40 tick / 1 tick |
| 站姿 `HOME` | 髋 0 / 大腿 0.9 / 小腿 −1.8（rad） |
| 摆幅 `AMP` | 髋 0 / 大腿 0.35 / 小腿 0.55（rad） |
| 相位 `PHASE` / 膝滞后 `LAG` | FL+RR 与 FR+RL 互差 π / 小腿滞后 0.5 rad |
| PD `KP` / `KD` | 25 / 60 / 60，0.5 / 1.0 / 1.0 |
| 力矩限幅 | 髋/大腿 ±23.7，小腿 ±45.43（N·m） |

## 实测结果

| 配置 | 4 s 终点 (x, y) | 4 s 位移 |
|---|---|---|
| Simovia 基线 `go2_trot_demo` | (+2.816, −1.772) | 2.82 m |
| 原生 MuJoCo（同物理配置） | (+2.80, −1.76) | 2.80 m |
| Simovia 目标域 `go2_trot_sim2sim` | (+3.348, −1.271) | 3.35 m |

前两行相差约 1.6 cm（端到端验证契约与控制律对齐）；第三行是只改物理后的结果。

## 适用范围

这是**同一控制律跨引擎迁移**，不是神经网络策略迁移：zoo 的 Go2 小跑是开环 CPG，没有策略权重可迁。如果要迁 PPO/模仿学习策略，`simovia/contract.py` 里的名字驱动契约（浮动机器人 48 维观测 / 12 维动作）就是为此准备的——把 `Go2Trot` 换成「契约适配器 + 策略前向」，两个 runner 都不用改。
