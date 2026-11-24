# SmolVLA 策略闭环评测（SO-101）

> Simovia Playground 分支 `demo/so101-policy-eval`。两路相机 + 语言指令输入，SmolVLA 按 chunk 输出关节目标，31.25Hz 闭环驱动 SO-101 分拣红蓝方块入盒。提供 **sim**（世界内推理）与 **sim2sim**（离线动作序列回放）两种模式。

## 看点

- **视觉-语言-动作闭环**：`cam_top` / `cam_left_wrist` 相机流 + 自然语言指令 → SmolVLA → chunk 关节目标，输出频率 31.25Hz。
- **成功判定独立**：控制器判定两块都入盒且释放后稳定保持 `success=true`；任务 zone 由内核另行校验。
- **sim2sim 回放**：`worlds/so101_policy_eval_sim2sim.yaml` 吃录制好的动作序列逐 tick 重放，用于隔离"策略输出"与"仿真环境"两侧的回归。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/so101_policy_eval.yaml` | 世界：SO-101 + 双相机 + 红蓝方块 + 成功 zone |
| `worlds/so101_policy_eval_sim2sim.yaml` | sim2sim 动作回放世界 |
| `controllers/so101_policy_eval.py` | 策略推理控制器（两模式共用） |

## 复现流程

```bash
git checkout demo/so101-policy-eval
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

python -m simovia run worlds/so101_policy_eval.yaml            # sim 推理模式
python -m simovia run worlds/so101_policy_eval_sim2sim.yaml    # sim2sim 回放模式
python -m simovia gui
python -m pytest tests/ -q
```

> 推理模式需要本机部署的推理服务（模型权重与端点配置见主仓库 README 的 SmolVLA 章节）；sim2sim 模式无需权重即可跑通物理链路。

## 常见问题

- **策略不收敛/方块掉盒外**：先跑 sim2sim 确认物理链路正常，再查推理端 chunk 频率与指令文本拼写。
- **相机流黑屏**：离屏渲染需 `python -m simovia doctor` 里「离屏渲染」项为 OK。
