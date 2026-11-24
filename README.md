# 独立手眼标定（AXB）

> Simovia Playground 分支 `demo/hand-eye`。与视觉分拣解耦的独立手眼标定演示：多姿态采样 → AXB 求解相机-腕变换 → 重投影验证 → 标定结果落盘供分拣 demo 复用。

## 看点

- **多姿态采样**：机械臂扫一组已知关节姿态，标定板在相机视野内取多组对应。
- **AXB 求解与验证**：解出的相机外参以重投影误差验收；结果带资产指纹落盘，下游（视觉分拣）加载时强校验。

## 文件

| 文件 | 说明 |
|---|---|
| `demo/hand_eye/` | demo 包：采样控制器、求解、验证与标定数据 |

## 复现流程

```bash
git checkout demo/hand-eye
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt -r demo/fruit_sorting/requirements.txt
python -m simovia doctor

# 运行入口以 demo/hand_eye/ 内的说明为准
python -m simovia gui
```

## 常见问题

- **标定结果对不上**：换臂/换夹爪后旧标定即失效（挂点几何变了），重新跑采样标定。
- **指纹校验失败**：标定文件按原始字节 SHA-256 校验——勿用改写换行符的工具保存资产。
