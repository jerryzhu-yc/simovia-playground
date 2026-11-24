# Panda 抓取：相位机 + 6D 位姿 IK

> Simovia Playground 分支 `demo/pick-cube`。Franka Panda 挂 OnRobot 2FG7 平行夹爪，从高位接近方块、直线下探、闭合夹起、抬升到空中成功区保持。

## 看点

- **相位机控制器**：`approach → descend → close → lift → hold` 五段相位，每段直线插值关节/笛卡尔目标。
- **6D 位姿 IK**：按目标位姿解臂形关节角，落点误差以内即可稳定夹取。
- **成功判定**：方块（cube）抬入任务 zone 且保持——世界 YAML 的 `task.success.zone` 由内核独立判定，控制器 `report_result` 另行回报。

## 文件

| 文件 | 说明 |
|---|---|
| `worlds/pick_cube.yaml` | 世界：Panda + 2FG7 + 桌面方块 + 成功 zone |
| `controllers/pick_place.py` | 相位机抓取控制器 |
| `simovia/grippers.py` | 末端夹爪装配（2FG7 / 2F-85 / UMI / LEAP Hand） |

## 复现流程

```bash
git checkout demo/pick-cube
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m simovia doctor

python -m simovia run worlds/pick_cube.yaml      # 期望：任务: 成功
python -m simovia gui                              # 3D 视口看抓取全程
python -m pytest tests/ -q
```

## 常见问题

- **方块滑落**：闭合保持相位给足 tick 再抬升；夹取稳定性依赖物体与指尖双侧接触摩擦。
- **换夹爪**：GUI「装备」页选末端执行器一键换装（2FG7 → 2F-85 → UMI → LEAP Hand），世界自动重建。
