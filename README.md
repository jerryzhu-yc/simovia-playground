# 视觉水果分拣（腕部 RGB + 手眼标定）

> Simovia Playground 分支 `demo/fruit-sorting`。机械臂腕部 RGB 相机实时视觉：HSV 分割 + 连通域给识别框，2.5D 反投影转世界坐标，香蕉/苹果/葡萄分类放入三个框，落框结果独立复核——6/6 全部通过。

## 看点

- **手眼标定闭环**：标定（AXB 求解）→ 视觉检测 → 反投影世界坐标 → 抓取放置，全流程在一个 demo 内完成。
- **独立复核**：每个水果落框后由任务判定复核，不依赖控制器自报成功。

## 文件

| 文件 | 说明 |
|---|---|
| `demo/fruit_sorting/` | demo 包：控制器、视觉模块、标定数据 |
| `demo/fruit_sorting/requirements.txt` | OpenCV 依赖清单（核心 requirements 不含） |

## 复现流程

```bash
git checkout demo/fruit-sorting
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt -r demo/fruit_sorting/requirements.txt
python -m simovia doctor

python -m simovia run demo/fruit_sorting/<世界>.yaml    # 见 demo 内 README 细节
python -m simovia gui                                    # 相机面板看实时视觉
```

> 该 demo 的世界与运行入口以 `demo/fruit_sorting/` 内的说明为准（含标定数据指纹校验逻辑：换行符差异会导致标定加载失败，Windows 下注意保持仓库文件原始字节）。

## 常见问题

- **识别不到水果**：HSV 阈值对光照敏感，保持默认场景灯配置。
- **标定加载失败**：标定文件按资产原始字节 SHA-256 做指纹——勿用会改写换行符的编辑器保存资产文件。
