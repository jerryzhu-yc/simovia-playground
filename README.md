# π0.5 策略闭环推理：G1 收拾毛毯

> Simovia Playground 分支 `demo/g1-cloth-policy`。π0.5（pi05 + LoRA，30k step）在与训练数据同源的 G1 叠布世界里自主完成「抓起毛毯 → 放进收纳盒 → 松手」，全程 31.25 Hz 闭环，没有脚本轨迹，也没有手柄输入。

## 看点

- **端到端 VLA 闭环**：第三人称 `cam_high` + 腕部 `cam_left_wrist` 两路 256×256 图像，加 16 维关节状态与语言指令 → π0.5 一次输出 10 帧动作 chunk（训练时 `action_horizon=10`），控制器逐 tick 回放一帧，每个 chunk 覆盖 0.32s 仿真时间。
- **推理独立进程**：openpi 的 jax/flax 环境和内核的 mujoco 环境互斥，worker 用定长二进制协议走 stdin/stdout，256×256 图像不经过 JSON/base64；worker 就绪前控制器不渲染，避免「恢复权重峰值」和「离屏渲染」同时抢显存。
- **成功判定独立**：布料质心进入盒内判定区、**并且**两侧夹爪开度都低于 0.2（真的松手了）并保持 0.5s 才算成功；否则 30s 仿真时间上限判失败，避免「夹着悬在盒口上方」被误判。
- **显存调优**：cuda 下用 XLA 平台分配器（按需 cudaMalloc/cudaFree，用完归还给驱动），仿真已占 1~2G 时仍能连续推理；`num_steps=50` 实测首次含编译约 3.8s、之后约 0.37s/次。

## 环境要求

| 组件 | 要求 | 说明 |
|---|---|---|
| 仿真侧 | Python 3.12（推荐；最低 3.11）+ `requirements.txt` | `python -m simovia doctor` 全绿再往下走 |
| 推理侧 | OpenPI（独立 venv：Python 3.11 / jax 0.5.3 / flax 0.10.2） | 与仿真侧依赖互斥（一个要 jax、一个要 mujoco），必须两套环境 |
| 硬件 | 可选 NVIDIA GPU，≥ 8GB 空闲显存 | `device: cuda` 约 0.37s/次；`device: cpu` 约 7s/次，能用但慢 |
| 权重 | `pi05_g1_cloth_lora` 微调 checkpoint，约 6GB | 训练产物，不随本仓库分发，需自行训练或从发布渠道获取 |

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/g1_cloth_policy_eval.yaml` | 世界：G1 + 双臂 2F85 + flex 布料 + 收纳盒 + 双相机，以及全部推理/评估参数 |
| `controllers/g1_cloth_policy_eval.py` | 闭环控制器：渲染观测、拉起推理 worker、逐 tick 回放 chunk、判成功 |
| `controllers/pi05_infer_worker.py` | π0.5 推理 worker（用 openpi 的 `.venv` 解释器运行） |
| `controllers/g1_cloth_teleop.py` | 基类：站姿 / 锁浮动基座 / 2F85 夹爪 / 布料合规抓持 / 相机渲染，遥操作场景共用 |
| `openpi/g1_cloth_config.patch` | 打在上游 openpi 上的配置补丁（数据解码 + 数据配置 + 训练配置），推理前必须应用 |

## 复现流程

### 1) 仿真环境

```bash
git checkout demo/g1-cloth-policy
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m simovia doctor      # 依赖 / 模型资产 / 离屏渲染 / 样例世界编译
```

### 2) OpenPI 推理环境（独立一套）

```bash
git clone https://github.com/Physical-Intelligence/openpi.git ~/openpi
cd ~/openpi
git checkout 981483d     # 本 demo 验证过的上游提交（补丁上下文按它生成）
git apply /path/to/simovia-playground/openpi/g1_cloth_config.patch
uv sync                  # Python 3.11 + jax[cuda12]==0.5.3 + flax 0.10.2 + lerobot(上游固定 rev 0cf8648)
```

> **补丁内容（上游 openpi 里没有这三样）：**
> 1. `_DecodeG1Images` —— 把 lerobot 解码出的 `(C,H,W) float32 [0,1]` 帧转成 openpi 要的 `(H,W,C) uint8`，并把只有两路的相机补齐成 pi0/pi05 固定要的三路（第三路黑图 + `image_mask=False`，缺了会在 `Observation.from_dict` 报 KeyError）。
> 2. `LeRobotG1ClothDataConfig` —— G1 叠布数据配置：16 维 state/action（左 7 关节 + 左夹爪 + 右 7 关节 + 右夹爪）、两路相机 `cam_high` / `cam_left_wrist`、关节用 delta 动作而夹爪用绝对值。
> 3. 训练配置 `pi05_g1_cloth_lora` —— `pi05=True`、`action_horizon=10`、`gemma_2b_lora` + `gemma_300m_lora`、LoRA 微调、`repo_id="local/g1_cloth_teleop"`、`prompt_from_task=True`。
>
> 推理阶段只按名字 `pi05_g1_cloth_lora` 取配置，所以这个名字必须存在于你的 openpi 里。打完补丁自检一行（打印出配置名即成功）：
>
> ```bash
> ~/openpi/.venv/bin/python -c "from openpi.training import config; print(config.get_config('pi05_g1_cloth_lora').name)"
> ```

### 3) 权重目录

```text
~/openpi/checkpoints/pi05_g1_cloth_lora/g1_cloth/30000/
├── params/                 # orbax 参数（约 6GB）
├── assets/                 # 归一化统计量等
└── _CHECKPOINT_METADATA
```

这份权重是在 `local/g1_cloth_teleop` 数据集上用上面的 `pi05_g1_cloth_lora`（pi05 + LoRA）微调 30k step 得到的；自行训练时产物目录形如 `checkpoints/pi05_g1_cloth_lora/<实验名>/<step>/`。

路径与 `worlds/g1_cloth_policy_eval.yaml` 里的 `args.checkpoint` 对应；换成自己的 checkpoint 时改这一行即可。

### 4) 跑起来

```bash
python -m simovia run worlds/g1_cloth_policy_eval.yaml     # 无头闭环推理
python -m simovia gui                                      # GUI：打开该世界 → 运行
```

推理进度（每次推理的耗时、chunk 形状、覆盖的仿真时长）会打印在**终端 / GUI 控制台**；worker 的详细日志写在 `args.worker_log`（默认 `/tmp/pi05_worker.log`）。

## YAML 参数速查（`robots[].args`）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `model` | `pi05_g1_cloth_lora` | openpi 训练配置名，必须在推理环境里存在 |
| `checkpoint` | `~/openpi/checkpoints/pi05_g1_cloth_lora/g1_cloth/30000` | 权重目录 |
| `python` | `~/openpi/.venv/bin/python` | openpi venv 解释器；Windows 填 `.../.venv/Scripts/python.exe` |
| `device` | `cuda` | `cuda` / `cpu`；cpu 约 7s/次 |
| `num_steps` | `50` | flow-matching 去噪步数；10 是训练默认值，显存紧张就调小 |
| `ticks_per_action` | `1` | 每个预测动作重复的 tick 数；1 = 严格 31.25Hz 回放 |
| `prompt` | `put the blanket in the box` | 必须与训练数据集的 task 文本完全一致 |
| `cam_size` | `256` | 策略输入图像边长，与训练一致，别改 |
| `max_sim_seconds` | `30` | 仿真时间上限（约 940 tick），超时判失败 |
| `success_box` | 见 YAML | 布料质心的落盒判定区（z 上限压在盒口以下） |
| `success_hold_seconds` | `0.5` | 判定条件需持续的时间 |
| `grip_release_threshold` | `0.2` | 两侧夹爪开度都低于此值才算真松手 |
| `worker_log` | `/tmp/pi05_worker.log` | 推理 worker 日志；**Windows 改成绝对路径**，如 `C:/temp/pi05_worker.log` |
| `dataset` | `~/桌面/g1_cloth_policy_eval_dataset` | 仅基类初始化用（本场景不写帧），给个可写目录即可 |

## 排障

- **worker 起不来 / 推理中断**：异常信息里会带上 worker 日志尾部（含退出码）；索引里的 `pi05_g1_cloth_lora` 不存在、checkpoint 路径错、`python` 指向的不是 openpi venv，都会在这一步报出来。
- **CUDA OOM**：已内置 `XLA_PYTHON_CLIENT_ALLOCATOR=platform`（按需分配、用完归还）。仍然紧张时：把 `num_steps` 降到 10，或关掉占显存的桌面程序，或 `device: cpu`。
- **策略不动 / 夹住不松手**：先确认 `prompt` 与数据集 task 文本完全一致，再确认 `cam_size`、两路相机位姿没被改动——策略看到的画面必须还在训练分布里。
- **首帧很慢**：首次推理包含 XLA 编译，CPU 上要几十秒甚至更久；`runtime.controller_timeout` 已放宽到 600s，之后每个 chunk 稳定推理一次。
- **想测泛化**：当前布料初始位姿固定在世界 YAML 里（训练分布中心）。手工挪动 `blanket` 的 `pos` 就能看到策略的泛化边界，换位置后失败属于预期。
