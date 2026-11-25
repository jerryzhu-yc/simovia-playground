# Simovia Playground

**每个分支 = 一个可独立复现的机器人 demo。** 本仓库是 [Simovia](https://github.com/jerryzhu-yc/simovia) 的演示场：`main` 分支放索引，其余分支各携带一个 demo 的世界文件、控制器脚本与详细复现流程，全部开箱即跑（机器人模型资产 `models/zoo/` 随仓库自带，无需联网下载）。

## Demo 分支索引

| 分支 | Demo | 一句话介绍 |
|---|---|---|
| `demo/lidar-nav-3d` | 3D 多线雷达建图 + 全屋覆盖清扫 | 16 线 960 束/帧 3D 雷达建出 RViz 风格彩虹点云，规划蛇形全覆盖路径把整间房拖一遍再回充 |
| `demo/lidar-nav-2d` | 2D 雷达建图 + 骨架导航 | 60 束平面激光 log-odds 建图，维诺骨架 + A* + 纯跟踪驶向目标 |
| `demo/pick-cube` | Panda 抓取 | 2FG7 夹爪相位机抓方块：接近-下探-闭合-抬升-入成功区 |
| `demo/rrp3-ik` | RRP 三轴臂 DH 逆运动学 | DH 表造的 RRP 机械臂，解析 IK 写关节目标走轨迹 |
| `demo/so101-sort` | SO-101 分拣 | SO-ARM100 家族桌面分拣：识别红色方块夹入框 |
| `demo/so101-policy-eval` | SmolVLA 策略闭环 | 双相机 + 语言指令驱动 SO-101，31.25Hz chunk 推理（sim / sim2sim 双模式） |
| `demo/g1-cloth` | G1 收拾毛毯遥操作 | PICO 手柄遥操作 G1 + 2F85 抓毯入盒，LeRobot 数据集采集/增强/回放/策略评测 |
| `demo/g1-cloth-policy` | G1 收拾毛毯 π0.5 策略闭环 | 双相机 + 语言指令驱动 π0.5（pi05 + LoRA）自主抓毯入盒，31.25Hz chunk 推理 |
| `demo/go2-sim2sim` | Go2 对角小跑 sim2sim | 同一份 CPG 控制律：MuJoCo 原生 mj_step vs Simovia，目标域只改控制周期/积分器/impratio/摩擦/重力 |
| `demo/cloth-folding` | G1 叠毛毯 | G1 全身关节策略叠桌上的毛毯 |
| `demo/fruit-sorting` | 视觉水果分拣 | 腕部 RGB + HSV 分割 + 手眼标定反投影，香蕉/苹果/葡萄分类入框（6/6） |
| `demo/hand-eye` | 独立手眼标定 | AXB 手眼标定全流程：采样-求解-验证-落盘复用 |
| `demo/maintenance-relay` | 三机协同维修 | Go2 × G1 × UR5e 接力：UR5e 装模块 → Go2 运输 → G1 装入导向槽按复位键 |
| `demo/diy-arm` | 自制连杆树机械臂 | YAML 连杆树从零造 RRP 臂 + 实时矩阵/位姿打印教学 |

## 通用复现流程（任意分支）

```bash
# 1) 克隆并切到目标 demo 分支
git clone https://github.com/jerryzhu-yc/simovia-playground.git
cd simovia-playground
git checkout demo/lidar-nav-3d          # ← 换成你想跑的分支

# 2) 建 Python 3.11+ 虚拟环境并装依赖
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt          # 视觉 demo 另装 demo/fruit_sorting/requirements.txt

# 3) 环境自检（依赖/模型资产/离屏渲染/样例世界编译）
python -m simovia doctor

# 4) 无头跑一遍（CI 同款）
python -m simovia run worlds/<该分支的世界>.yaml

# 5) 桌面 GUI 可视化（3D 视口 + 雷达建图 + 3D 点云等面板）
python -m simovia gui     # 打开 worlds/<世界>.yaml → 运行
```

各分支根目录的 `README.md` 有该 demo 的详细说明、参数表与排障提示。平台本身的完整文档（世界文件格式、控制器 API、MCP、GUI、RL 接口）见 [simovia 主仓库](https://github.com/jerryzhu-yc/simovia)。

## 测试

```bash
python -m pytest tests/ -q
```
