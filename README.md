# π0.5 策略闭环推理：G1 收拾毛毯

> Simovia Playground 分支 `demo/g1-cloth-policy`。π0.5（pi05 + LoRA，30k step）在与训练数据同源的 G1 叠布世界里自主完成「抓起毛毯 → 放进收纳盒 → 松手」，全程 31.25 Hz 闭环，没有脚本轨迹、也没有手柄输入。

## 看点

- **端到端 VLA 闭环**：第三人称 `cam_high` + 腕部 `cam_left_wrist` 两路 256×256 图像，加 16 维关节状态与语言指令 → π0.5 一次输出 10 帧动作 chunk（训练时 `action_horizon=10`），控制器逐 tick 回放一帧，每个 chunk 覆盖 0.32s 仿真时间。
- **推理独立进程**：openpi 的 jax/flax 环境和内核的 mujoco 环境互斥，worker 用定长二进制协议走 stdin/stdout，256×256 图像不经过 JSON/base64；worker 就绪前控制器不渲染，避免「恢复权重峰值」和「离屏渲染」同时抢显存。
- **成功判定独立**：布料质心进入盒内判定区、**并且**两侧夹爪开度都低于 0.2（真的松手了）并保持 0.5s 才算成功；否则 30s 仿真时间上限判失败，避免「夹着悬在盒口上方」被误判。
- **显存调优**：cuda 下用 XLA 平台分配器（按需 cudaMalloc/cudaFree，用完归还给驱动），仿真已占 1~2G 时仍能连续推理；`num_steps=50` 实测首次含编译约 3.8s、之后约 0.37s/次。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/g1_cloth_policy_eval.yaml` | 世界：G1 + 双臂 2F85 + flex 布料 + 收纳盒 + 双相机，以及全部推理/评估参数 |
| `controllers/g1_cloth_policy_eval.py` | 闭环控制器：渲染观测、拉起推理 worker、逐 tick 回放 chunk、判成功 |
| `controllers/pi05_infer_worker.py` | π0.5 推理 worker（用 openpi 的 `.venv` 解释器运行） |
| `controllers/g1_cloth_teleop.py` | 基类：站姿 / 锁浮动基座 / 2F85 夹爪 / 布料合规抓持 / 相机渲染，遥操作场景共用 |

## 复现流程

```bash
git checkout demo/g1-cloth-policy
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

# 1) 准备 π0.5 推理环境（OpenPI，jax/flax，与内核环境互斥，需单独一套）
#    按 OpenPI 文档建出 ~/openpi/.venv，并准备训练产出的 checkpoint。
#    权重约 6GB，不随本仓库分发；
# 2) 修改 worlds/g1_cloth_policy_eval.yaml 的 robots[].args：
#    checkpoint（权重目录）/ python（openpi 解释器）/ device（cpu|cuda）/ num_steps
python -m simovia run worlds/g1_cloth_policy_eval.yaml     # 无头闭环推理
python -m simovia gui                                      # GUI：打开该世界 → 运行
python -m pytest tests/ -q
```

## 排障

- **worker 起不来 / 推理中断**：异常信息里会带上 worker 日志（`args.worker_log`，默认 `/tmp/pi05_worker.log`）尾部；推理进度统一走 stderr，因为 MCP / GUI 模式下 stdout 是 JSON-RPC 协议流，print 到 stdout 会被吞掉。
- **CUDA OOM**：已内置 `XLA_PYTHON_CLIENT_ALLOCATOR=platform`；显存仍然紧张时把 `num_steps` 降到 10（训练默认值），或直接 `device: cpu`（约 7s/次，能用但慢）。
- **策略不动 / 夹住不松手**：先确认 `prompt` 与训练集 task 文本完全一致（默认 `put the blanket in the box`），再确认 `cam_size`、两路相机位姿没被改动——策略看到的画面必须还在训练分布里。
- **首帧很慢**：首次推理包含 XLA 编译，CPU 上要几十秒甚至更久，`runtime.controller_timeout` 已放宽到 600s；之后稳定在每次 chunk 一次推理。
- **想测泛化**：当前布料初始位姿固定在世界 YAML 里（训练分布中心）。手工挪动 `blanket` 的 `pos` 就能看到策略的泛化边界，换位置后失败属于预期。
