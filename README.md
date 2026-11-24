# RRP 三轴机械臂：DH 建模 + 解析逆运动学

> Simovia Playground 分支 `demo/rrp3-ik`。用 YAML 连杆树从零造一台 RRP（两转一移）三轴机械臂，DH 参数建运动学，解析逆运动学驱动末端走轨迹——机器人学入门教具。

## 看点

- **World as Code 造机器人**：`robots[].links` 连杆树（parent / pos / rpy / 几何 / 关节）直接编译成 MJCF，不写一行 XML。
- **DH 正/逆运动学**：控制器内置 DH 表解析 IK，末端沿直线轨迹插值运动；GUI「造机器人」页同步显示每个连杆的 R_rel / R_world 旋转矩阵。
- **教学向**：`robot.step()` 循环里逐帧打印关节角/位姿，配合 GUI 坐标轴理解 R = Rz·Ry·Rx。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/rrp3_ik.yaml` | 世界：RRP 连杆树机械臂 + 目标轨迹 |
| `controllers/rrp3_ik.py` | DH 解析 IK 控制器 |
| `simovia/robot_spec.py` | DH/连杆树编译进 MuJoCo（骨架把移动关节画成滑块+导轨） |

## 复现流程

```bash
git checkout demo/rrp3-ik
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

python -m simovia run worlds/rrp3_ik.yaml
python -m simovia gui            # 打开世界 → 运行，3D 看臂形轨迹
python -m pytest tests/ -q
```

## 常见问题

- **IK 无解**：目标点超出工作空间半径（两转臂长 + 移动行程）；控制器会钳到可达域。
- **关节抖动**：检查解析 IK 的奇异位形（臂完全伸直）附近的轨迹插值。
