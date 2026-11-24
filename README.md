# 自制连杆树机械臂（教学）

> Simovia Playground 分支 `demo/diy-arm`。用 YAML 连杆树从零拼一台自制机械臂，控制器随机摆动关节并实时打印各连杆的相对/世界旋转矩阵与位姿——「从零造机器人」功能的最小示例。

## 看点

- **连杆树即机器人**：`links` 数组（parent / pos / rpy / box 几何 / hinge 关节）直接编译成 MJCF，几分钟从空文件到会动的臂。
- **矩阵级教学输出**：控制器逐帧打印 R_rel / R_world 与末端位姿，配合 GUI「造机器人」页的 3D 坐标轴理解旋转。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/diy_arm.yaml` | 世界：连杆树机械臂 |
| `controllers/diy_arm_log.py` | 随机摆动 + 矩阵/位姿打印控制器 |

## 复现流程

```bash
git checkout demo/diy-arm
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

python -m simovia run worlds/diy_arm.yaml     # 终端滚动打印关节与矩阵
python -m simovia gui                          # 3D 视口看摆动
python -m pytest tests/ -q
```

## 常见问题

- **改连杆后臂形不对**：`rpy` 是弧度、`pos` 是连杆系内偏移；改完用 `python -m simovia inspect worlds/diy_arm.yaml` 核对关节表。
