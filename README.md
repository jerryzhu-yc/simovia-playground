# 2D 雷达建图 + 维诺骨架导航

> Simovia Playground 分支 `demo/lidar-nav-2d`。小车顶一圈 60 束平面激光，巡逻建图 → 维诺骨架 + A* 规划 → 纯跟踪驶向目标。是 `demo/lidar-nav-3d` 的 2D 前身，对照着看能直观理解"为什么扫地机需要 3D 雷达"。

## 看点

- **log-odds 占据栅格**：内核 `LidarMapper` 逐束 Bresenham raycasting（穿越打自由、命中打占据），保守建图（无回波不更新）。
- **规划三件套**：可通行区障碍膨胀 → Zhang-Suen 细化出障碍通道正中的 1px 维诺骨架 → 起终点吸附骨架 + A* 搜路 → 纯跟踪（LOOKAHEAD 0.22m）沿线行驶。
- **GUI 雷达建图面板**：占据栅格实时填充，骨架（蓝）/A* 路径（黄）/巡逻框（棕）/起终点（橙/绿）矢量叠加，可直观判断路径是否贴骨架走。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/lidar_nav.yaml` | 世界：房间 + 巡逻路径 + 小车（车顶 2D 雷达） |
| `controllers/lidar_nav.py` | 控制器：巡逻建图 → 骨架 A* → 纯跟踪 |
| `simovia/kernel/mapping.py` | 内核 2D 建图器（`LidarMapper`） |
| `simovia/gui/map_panel.py` | GUI 俯视建图面板 |

## 复现流程

```bash
git checkout demo/lidar-nav-2d
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

# 1) 无头跑
python -m simovia run worlds/lidar_nav.yaml

# 2) GUI 可视化：打开 worlds/lidar_nav.yaml → 运行
python -m simovia gui
#    「俯视建图」页签看栅格填充与骨架/A* 叠加层

# 3) 回归
python -m pytest tests/ -q
```

## 常见问题

- **路径穿障碍**：确认 `INFLATE` 安全带 ≥ 底盘半径 + 切角余量；骨架必须经 `segment_clear` 接入起终点而不是就近吸附。
- **车原地跳舞**：路径太稀（拐点间距 > 3m）会让纯跟踪 carrot 点翻转——用 `densify` 加密到 0.1m 间距。
