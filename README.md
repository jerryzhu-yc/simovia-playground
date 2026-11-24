# G1 叠毛毯

> Simovia Playground 分支 `demo/cloth-folding`。宇树 G1 人形机器人把桌上的毛毯对折收整——柔性物体（布料）接触/摩擦主导的全身操作演示。

## 看点

- **柔性物体仿真**：毛毯为可变形体，G1 双臂按压-推送-对折的动作序列全程靠接触与摩擦完成。
- **全身关节控制**：控制器直接写 G1 上肢 + 腰部关节目标，相位化推进折毯流程。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/g1_cloth_fold.yaml` | 世界：G1 + 桌 + 毛毯 |
| `demo/cloth_folding/controller.py` | 折毯相位控制器 |

## 复现流程

```bash
git checkout demo/cloth-folding
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

python -m simovia run worlds/g1_cloth_fold.yaml
python -m simovia gui              # 3D 视口看折毯全程
python -m pytest tests/ -q
```

## 常见问题

- **毛毯穿透桌面**：布料网格与桌面的接触参数在模型内标定，勿在 YAML 覆盖 `condim`/`friction`。
