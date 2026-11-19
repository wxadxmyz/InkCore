# -*- coding: utf-8 -*-
"""v2.1.0 测试：窗口自适应几何计算 + 品牌资源存在性。

运行： python3 -m pytest tests/test_window.py -q
不依赖 GUI / API Key / 网络。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import desktop_app as da


class TestWindowGeometry:
    def test_large_screen_keeps_design_size(self):
        # 1920×1080 的工作区（扣任务栏约 1920×1040）：应维持设计尺寸 1280×820
        w, h, mn = da.compute_window_geometry(1920, 1040)
        assert (w, h) == (1280, 820)
        assert mn == (960, 620)

    def test_small_laptop_shrinks_and_fits(self):
        # 1366×768 工作区约 1366×728：窗口必须缩小且完整落在工作区内
        work_w, work_h = 1366, 728
        w, h, mn = da.compute_window_geometry(work_w, work_h)
        assert w < 1280 and h < 820, "小屏应缩小窗口"
        assert w <= work_w and h <= work_h, "窗口不得超出工作区"
        # 宽高比与设计比保持一致（误差 1%）
        assert abs(w / h - 1280 / 820) < 0.02
        # min_size 不得超过实际窗口
        assert mn[0] <= w and mn[1] <= h

    def test_tiny_screen_still_usable(self):
        # 1024×600 工作区约 1024×560
        work_w, work_h = 1024, 560
        w, h, mn = da.compute_window_geometry(work_w, work_h)
        assert w >= 480 and h >= 360, "窗口不应小到不可用"
        assert w <= work_w and h <= work_h
        assert mn[0] <= w and mn[1] <= h

    def test_min_size_never_exceeds_window(self):
        for ww, wh in [(800, 500), (1024, 560), (1280, 700), (1920, 1040), (2560, 1400)]:
            w, h, mn = da.compute_window_geometry(ww, wh)
            assert mn[0] <= w and mn[1] <= h, f"{ww}x{wh}: min_size 越界"

    def test_monotonic(self):
        # 工作区越大，窗口不应变小
        prev = 0
        for wh in [500, 560, 700, 900, 1040, 1400]:
            w, h, _ = da.compute_window_geometry(1920, wh)
            assert h >= prev, "窗口高度应随可用高度单调不减"
            prev = h


class TestBrandAssets:
    def test_icon_files_exist(self):
        for name in ["icon.png", "icon.ico"]:
            assert (ROOT / "static" / name).exists(), f"缺少 static/{name}"

    def test_wizard_images_exist_and_size(self):
        from PIL import Image
        big = Image.open(ROOT / "static" / "wizard-image.bmp")
        small = Image.open(ROOT / "static" / "wizard-small.bmp")
        assert big.size == (164, 314), "Inno Setup 向导大图必须为 164×314"
        assert small.size == (64, 64), "Inno Setup 向导小图必须为 64×64"

    def test_installer_references_wizard_images(self):
        iss = (ROOT / "installer.iss").read_text(encoding="utf-8")
        assert "WizardImageFile=static\\wizard-image.bmp" in iss
        assert "WizardSmallImageFile=static\\wizard-small.bmp" in iss
