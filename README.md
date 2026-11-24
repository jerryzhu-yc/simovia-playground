# SO-101 桌面分拣：抓红色方块入框

> Simovia Playground 分支 `demo/so101-sort`。SO-ARM100 家族开源机械臂 SO-101，在桌面上识别并抓取红色方块放入收集框——策略评测（`demo/so101-policy-eval`）的规则基线版本。

## 看点

- **SO-101 模型库直出**：`zoo://` 引用内置模型资产，世界 YAML 一个字段上机器人。
- **规则分拣控制器**：固定观察 → 俯身 → 闭合 → 抬起 → 移框 → 释放的相位机，验证模型/夹爪/接触链路。
- **与策略评测同构**：本 demo 的世界是 SmolVLA 策略评测（`so101_policy_eval.yaml`）的姊妹版，规则控制跑通即策略环境的物理基线成立。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/so101_sort.yaml` | 世界：SO-101 + 红方块 + 收集框 |
| `controllers/so101_pick_red.py` | 规则分拣控制器 |

## 复现流程

```bash
git checkout demo/so101-sort
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

python -m simovia run worlds/so101_sort.yaml
python -m simovia gui               # 3D 视口看分拣全程
python -m pytest tests/ -q
```

## 常见问题

- **方块没夹稳**：闭合相位给足 tick；SO-101 夹爪指面摩擦参数在模型内固定，勿在 YAML 重复覆盖。
