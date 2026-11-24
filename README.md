# 3D 多线雷达建图 + 全屋覆盖清扫（扫地机器人）

> Simovia Playground 分支 `demo/lidar-nav-3d`。一台车顶装 16 线 3D 雷达的扫地机器人，在 6.4m × 4.8m 的居家房间（床/衣柜/餐桌椅/沙发/茶几/电视柜/地毯）里**巡逻建图 → 规划全屋蛇形覆盖路线 → 把整个场地拖一遍 → 回充到任务目标点**。

## 看点

- **3D 多线雷达**：16 通道（-25°~+30° 垂直视场）× 60 束 = **960 束/帧**，内核 `PointCloudMapper` 把命中点离散成 0.04m 体素累积成全量 3D 点云——GUI 的「3D 点云」页签按高度彩虹着色渲染成 RViz 风格立体点云（墙身、桌面底面、桌下地面分层可见）。
- **高度带语义（2D 雷达的盲区故事）**：俯视占据栅格只投影 z ∈ (0.02, 0.18)（扫地机可撞带）内的命中——床裙、椅腿横撑这类**悬空低矮障碍**只有 3D 雷达的低仰角通道能扫到，2D 平面激光（挂点 ~0.07m）永远扫不到、扫地机必撞。本 demo 的床裙/椅横撑几何就为此设计。
- **全屋蛇形覆盖**：规划阶段把可通行区（自由 − 0.30m 障碍膨胀安全带）按 0.34m 间距切成 y 条带、逐带蛇形往返，条带之间用 8 邻接栅格 A* 连接（绕开家具安全带），收尾接一段回充路线——"把所有场地都拖一遍"。
- **三阶段控制器**：EXPLORE（大环巡逻喂图）→ PLAN（覆盖规划，原地暂停）→ NAVIGATE（0.24 m/s 走完全部覆盖线 + 回充，到点 `report_result(True)` 并报告预估覆盖率）。
- **与内核同源建图**：控制器直接 `import` 内核 `PointCloudMapper`——GUI 雷达建图面板、3D 点云面板与控制器决策用的是同一张栅格、同一份语义。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/lidar_nav3d.yaml` | 世界：居家房间家具几何 + sweeper（车顶 3D 雷达，`models/sweeper.xml`）+ 任务成功 zone |
| `controllers/lidar_nav3d.py` | 三阶段控制器（建图 → 覆盖规划 → 纯跟踪清扫 + 回充） |
| `simovia/kernel/mapping.py` | 内核 3D 点云建图器（体素 + 高度带俯视投影 + 渲染槽位） |
| `simovia/gui/pointcloud_panel.py` | GUI 3D 点云面板（黑底彩虹、拖拽旋转/滚轮缩放/双击复位） |
| `simovia/gui/map_panel.py` | GUI 俯视建图面板（占据栅格 + 覆盖线/路线/骨架叠加层） |
| `tests/test_lidar3d.py` | 16 通道回波真值、建图、规划回归测试 |
| `scripts/make_lidar3d_video.py` | 三视图演示视频合成脚本（MuJoCo 实车 × 3D 点云 × 2D 建图导航） |

## 复现流程

```bash
git checkout demo/lidar-nav-3d
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor          # 依赖/模型/离屏渲染自检

# 1) 无头跑完整 episode（约 1 万 tick：巡逻 ~3300 + 覆盖 ~6500）
python -m simovia run worlds/lidar_nav3d.yaml
#    期望末尾输出：任务: 成功（机器人回到 zone）
#    控制器回报："全屋蛇形清扫完成：可通行 N 格 / 约 30 条覆盖线（间距 0.34m）预估覆盖 9x%"

# 2) GUI 可视化
python -m simovia gui
#    打开 worlds/lidar_nav3d.yaml → 运行：
#    - 主视口：3D 实车行驶，场景内同步显示内核累积的点云槽位
#    - 「俯视建图」页签：占据栅格逐帧填充 + 规划瞬间出现
#      青色覆盖线（cover）/ 黄色路线（path）/ 蓝色骨架 / 棕色巡逻框
#    - 「3D 点云」页签：黑底彩虹立体点云（左键旋转/滚轮缩放/双击复位）

# 3) 回归测试
python -m pytest tests/test_lidar3d.py tests/test_gui.py -q

# 4)（可选）合成三视图演示视频（需 ffmpeg）
QT_QPA_PLATFORM=offscreen MUJOCO_GL=egl python scripts/make_lidar3d_video.py
```

## 参数速查（`controllers/lidar_nav3d.py`）

| 常量 | 默认 | 说明 |
|---|---|---|
| `COVER_STEP` | 0.34 m | 蛇形条带间距：调大漏扫、调小路线变长 |
| `COVER_MIN_SEG` | 0.30 m | 单条覆盖线最短长度（更碎的段跳过，转弯不值） |
| `V_COVER` | 0.24 m/s | 覆盖巡航速度（转弯频繁，别超过巡逻速度太多） |
| `INFLATE` | 0.30 m | 障碍膨胀安全带（底盘 r=0.14 + 纯跟踪切角余量） |
| `EXPLORE_TIMEOUT` | 7000 tick | 建图阶段兜底（正常巡逻一圈 ~3300） |
| `NAV_TIMEOUT` | 18000 tick | 覆盖阶段兜底（相对进入覆盖的时刻起算，任务上限 20000） |

## 常见问题

- **车在某个家具旁反复顶死**：调大 `INFLATE` 或调低 `V_COVER`；多半是纯跟踪切角量盖不住安全带。
- **俯视建图面板没有覆盖线**：覆盖线在 PLAN 阶段一次性发布，巡逻没走完不会出现；`EXPLORE_TIMEOUT` 后兜底也会触发规划。
- **3D 点云页签空白**：雷达数据没喂进来前显示"等待 3D 点云数据…"，运行起来即可。
