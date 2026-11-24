"""lidar_nav3d 演示视频合成：三视图同帧合成 + ffmpeg 加速编码。

布局（1280x720）：
- 左半 640x720：MuJoCo 3D 实车行驶（相机跟随扫地机，场景内同步显示
  内核累积的 3D 点云槽位）
- 右上 640x360：3D 点云面板（gui/pointcloud_panel，黑底彩虹高度着色，
  RViz 风格，与 GUI 同款渲染）
- 右下 640x360：俯视建图 + 覆盖导航面板（gui/map_panel，占据栅格 +
  控制器叠加层：覆盖线/路线/骨架/巡逻）

数据链路与 GUI 完全一致：直接复用 RadarMapPanel / PointCloudView 两个
Qt 部件（offscreen 平台），每 STRIDE 个控制 tick 抓一帧，三个视图取同
一 control tick 的状态合成一张 1280x720 帧，最后 ffmpeg 以 30fps 编码
（STRIDE=5 → 约 4.8 倍速）。

用法：
    QT_QPA_PLATFORM=offscreen MUJOCO_GL=egl python scripts/make_lidar3d_video.py \
        [--world worlds/lidar_nav3d.yaml] [--stride 5] [--out site/public/assets/demos/lidar_nav3d.mp4]
"""
import argparse
import base64
import math
import os
import subprocess
import sys
import zlib

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

W, H = 1280, 720
LW, PH, MH = 640, 360, 360        # 左视宽 / 右上高 / 右下高
STRIDE = 5                         # 每 N 个控制 tick 抓一帧（≈N 倍速）
FPS = 30


def _qimage_rgb(img) -> np.ndarray:
    """QImage -> (h,w,3) uint8（处理 bytesPerLine 对齐）。"""
    from PySide6.QtGui import QImage
    img = img.convertToFormat(QImage.Format.Format_RGB888)
    h, w, bpl = img.height(), img.width(), img.bytesPerLine()
    buf = np.frombuffer(img.constBits(), dtype=np.uint8, count=bpl * h)
    rgb = buf.reshape(h, bpl)[:, :w * 3].reshape(h, w, 3)
    return np.ascontiguousarray(rgb)


def _label(canvas: np.ndarray, x: int, y: int, text: str, size=15, pad=6):
    """在帧上画一个半透明条 + 白字标签（用 QPainter 直接在 numpy 缓冲上）。"""
    from PySide6.QtGui import QColor, QImage, QPainter, QPen
    img = QImage(canvas.data, canvas.shape[1], canvas.shape[0],
                 canvas.strides[0], QImage.Format.Format_RGB888)
    p = QPainter(img)
    try:
        from PySide6.QtGui import QFont
        f = QFont()
        f.setPointSize(size)
        f.setBold(True)
        p.setFont(f)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(text)
        p.fillRect(x - pad, y - size - pad, tw + 2 * pad, size + 2 * pad,
                   QColor(0, 0, 0, 150))
        p.setPen(QPen(QColor(255, 255, 255)))
        p.drawText(x, y, text)
    finally:
        p.end()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="worlds/lidar_nav3d.yaml")
    ap.add_argument("--stride", type=int, default=STRIDE)
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--frames-dir", default="/tmp/lidar3d_frames")
    ap.add_argument("--out", default="site/public/assets/demos/lidar_nav3d.mp4")
    args = ap.parse_args()

    import mujoco
    from PySide6.QtWidgets import QApplication

    from simovia.gui.map_panel import RadarMapPanel
    from simovia.gui.pointcloud_panel import PointCloudView
    from simovia.kernel.mapping import PointCloudMapper
    from simovia.kernel.sim import Simulation
    from simovia.kernel.task import root_freejoint_qadr
    from simovia.render import render_offscreen
    from simovia.world.schema import load_world

    app = QApplication([])                        # offscreen 平台
    pc_view = PointCloudView()
    pc_view.resize(LW, PH)
    map_view = RadarMapPanel()
    map_view.resize(LW, MH)
    pc_view.show()
    map_view.show()
    app.processEvents()

    os.makedirs(args.frames_dir, exist_ok=True)
    for f in os.listdir(args.frames_dir):
        os.remove(os.path.join(args.frames_dir, f))

    spec = load_world(args.world)
    rname = spec.robots[0].name
    renderer = None
    cam = mujoco.MjvCamera()
    frame_idx, phase_text = [0], ["EXPLORE 建图巡逻"]

    def _snapshot(sim) -> dict:
        """复刻 MCP _tool_lidar_map 的 payload（maps/poses/overlays/pc）。"""
        maps, poses, pcs = {}, {}, {}
        for rn, mapper in sim.lidar_mappers.items():
            meta = mapper.meta()
            g, pr = mapper.grid(), mapper.prob()
            maps[rn] = {**meta,
                        "grid": base64.b64encode(zlib.compress(g.tobytes(), 1)).decode("ascii"),
                        "prob": base64.b64encode(zlib.compress(pr.tobytes(), 1)).decode("ascii")}
            if isinstance(mapper, PointCloudMapper):
                pts = mapper.pointcloud(max(1, min(len(mapper.vox), 120000)))
                arr = np.empty((len(pts), 6), dtype=np.float32)
                for i, q in enumerate(pts):
                    r, g2, b = mapper._height_rgb(q[2])
                    arr[i] = (q[0], q[1], q[2], r, g2, b)
                pcs[rn] = {"seq": mapper.seq, "voxel": len(mapper.vox),
                           "half": mapper.RENDER_HALF, "n": len(pts),
                           "points": base64.b64encode(
                               zlib.compress(arr.tobytes(), 1)).decode("ascii")}
            ridx = sim.index.robots[rn]
            qadr = root_freejoint_qadr(sim.model, ridx)
            if qadr is not None:
                x, y, _z, qw, qx, qy, qz = (float(v) for v in
                                            sim.data.qpos[qadr:qadr + 7])
                poses[rn] = [x, y, math.atan2(
                    2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))]
        overlays = {r: {k: {"segments": [list(s) for s in v["segments"]],
                           "points": [list(p) for p in v["points"]]}
                        for k, v in d.items()}
                    for r, d in sim.controller_overlays.items()}
        out = {"available": True, "maps": maps, "poses": poses,
               "overlays": overlays}
        if pcs:
            out["pc"] = pcs
        return out

    def _grab(sim) -> None:
        nonlocal renderer
        # ---- 左：MuJoCo 3D 实车（相机跟随扫地机）
        ridx = sim.index.robots[rname]
        qadr = root_freejoint_qadr(sim.model, ridx)
        x, y, z, qw, qx, qy, qz = (float(v) for v in sim.data.qpos[qadr:qadr + 7])
        yaw = math.atan2(2.0 * (qw * qz + qx * qy),
                         1.0 - 2.0 * (qy * qy + qz * qz))
        cam.lookat[:] = [x, y, 0.35]
        cam.distance = 3.6
        cam.azimuth = math.degrees(yaw) + 100.0     # 车尾追随机位
        cam.elevation = -28.0
        if renderer is None:
            renderer = mujoco.Renderer(sim.model, H, LW)
        rgb3d = render_offscreen(sim.model, sim.data, LW, H,
                                  renderer=renderer, free_cam=cam)
        # ---- 右上/右下：Qt 部件（喂同款数据后 grab）
        data = _snapshot(sim)
        pc_view.update_pc(next(iter(data.get("pc", {}).values()), None))
        map_view.update_map(data)
        if "cover" in str(data.get("overlays", {})) or sim.tick > 4000:
            phase_text[0] = "PLAN 全屋覆盖规划 → NAVIGATE 蛇形清扫"
        app.processEvents()
        pc_rgb = _qimage_rgb(pc_view.grab().toImage())
        map_rgb = _qimage_rgb(map_view.grab().toImage())
        # ---- 合成 + 标签
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[:, :LW] = rgb3d
        canvas[:PH, LW:] = pc_rgb
        canvas[PH:, LW:] = map_rgb
        _label(canvas, 14, 30, f"MuJoCo 3D 实车行驶 · {phase_text[0]}")
        _label(canvas, LW + 14, 30, "3D 点云建图（RViz 风格彩虹着色）")
        _label(canvas, LW + 14, PH + 30, "俯视占据栅格 + 蛇形覆盖导航")
        _label(canvas, 14, H - 16, f"tick {sim.tick} · 4.8x", size=12)
        from PySide6.QtGui import QImage
        img = QImage(canvas.data, W, H, canvas.strides[0],
                     QImage.Format.Format_RGB888)
        img.save(f"{args.frames_dir}/{frame_idx[0]:06d}.png")
        frame_idx[0] += 1

    with Simulation(spec) as sim:
        stats = sim.run(on_tick=lambda: (
            _grab(sim) if sim.tick > 0 and sim.tick % args.stride == 0 else None))
    print(f"episode 完成：{stats['ticks']} ticks，"
          f"抓帧 {frame_idx[0]} 张 → {args.frames_dir}")

    # ---- ffmpeg：PNG 序列 -> H.264（faststart 便于网页边下边播）
    n = frame_idx[0]
    dur = n / args.fps
    cmd = ["ffmpeg", "-y", "-framerate", str(args.fps),
           "-i", f"{args.frames_dir}/%06d.png",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
           "-movflags", "+faststart", args.out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg 失败: {r.stderr[-500:]}")
    size = os.path.getsize(args.out) / 1e6
    print(f"视频已生成 {args.out}：{n} 帧 / {dur:.0f}s @ {args.fps}fps "
          f"（{args.stride} tick/帧 ≈ {args.stride * 0.032 * args.fps:.1f}x 加速）"
          f"，{size:.1f} MB")


if __name__ == "__main__":
    main()
