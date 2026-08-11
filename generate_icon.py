# -*- coding: utf-8 -*-
"""生成墨核 AI Studio 的应用图标（PNG + ICO）。
设计：大圆角紫色渐变底 + 白色「原子核」标记（中心核 + 三条轨道 + 轨道光点），
无文字、无字体依赖，跨平台渲染稳定。"""
import math
from PIL import Image, ImageDraw

W = 1024          # 输出分辨率
S = W * 2         # 2x 超采样
RADIUS = 220 * 2  # 圆角半径

def rounded_rect(size, radius, fill):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=fill)
    return img

def gradient_base(size):
    """竖直紫渐变 + 轻微噪点破阶 + 径向高光。"""
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)
    c1 = (75, 45, 195)
    c2 = (139, 92, 246)
    for y in range(size):
        t = y / (size - 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line((0, y, size, y), fill=(r, g, b))
    img = img.convert('RGBA')
    # 噪点破阶
    noise = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    nd = ImageDraw.Draw(noise)
    for i in range(12000):
        x = (hash(str(i)) & 0x7FFFFFFF) % size
        y = (hash(str(i * 7)) & 0x7FFFFFFF) % size
        nd.point((x, y), fill=(255, 255, 255, 6))
    img = Image.alpha_composite(img, noise)
    # 径向高光
    overlay = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    cx, cy = size // 2, size // 3
    for r in range(size // 2, 0, -2):
        alpha = int(22 * (r / (size // 2)) ** 2)
        od.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, alpha))
    return Image.alpha_composite(img, overlay)

def ellipse_ring(size, cx, cy, rw, rh, thickness, color):
    """在透明层上画一个椭圆环。"""
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for i in range(thickness):
        weight = 1 - abs((i / (thickness - 1)) - 0.5) * 1.6
        a = max(0, int(color[3] * weight))
        c = (color[0], color[1], color[2], a)
        draw.ellipse((cx - rw / 2 - i, cy - rh / 2 - i,
                      cx + rw / 2 + i, cy + rh / 2 + i), outline=c)
    return layer

def rotate_layer(layer, angle):
    return layer.rotate(angle, resample=Image.BICUBIC, expand=False,
                        center=(layer.width // 2, layer.height // 2))

def make_icon():
    base = gradient_base(S)
    cx, cy = S // 2, S // 2

    atom = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ring_w, ring_h = S * 0.70, S * 0.26
    thickness = 26
    white = (255, 255, 255, 255)
    for angle in (0, 60, 120):
        ring = ellipse_ring(S, cx, cy, ring_w, ring_h, thickness, white)
        ring = rotate_layer(ring, angle)
        atom = Image.alpha_composite(atom, ring)

    # 中心发光
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(160, 0, -3):
        a = int(55 * math.exp(-r / 45))
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, a))
    base = Image.alpha_composite(base, glow)

    # 中心核
    core = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    cd.ellipse((cx - 82, cy - 82, cx + 82, cy + 82), fill=(255, 255, 255, 255))
    cd.ellipse((cx - 44, cy - 44, cx + 44, cy + 44), fill=(215, 215, 255, 255))
    base = Image.alpha_composite(base, core)

    # 轨道光点
    dot_layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dot_layer)
    dot_r = 32
    dx, dy = cx + ring_w // 2, cy
    dd.ellipse((dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r), fill=(255, 255, 255, 255))
    for r in range(70, dot_r, -3):
        a = int(60 * (1 - (r - dot_r) / (70 - dot_r)))
        dd.ellipse((dx - r, dy - r, dx + r, dy + r), fill=(255, 255, 255, a))
    dot_layer = rotate_layer(dot_layer, 30)
    atom = Image.alpha_composite(atom, dot_layer)

    base = Image.alpha_composite(base, atom)

    # 圆角蒙版
    mask = rounded_rect(S, RADIUS, (255, 255, 255, 255))
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(base, (0, 0), mask)
    return out.resize((W, W), Image.LANCZOS)

if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    out = make_icon()
    png_path = os.path.join(here, "static", "icon.png")
    ico_path = os.path.join(here, "static", "icon.ico")
    out.save(png_path)
    # 生成 Windows 推荐的全套图标尺寸，保证在不同 DPI/视图下都清晰
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [out.resize((s, s), Image.LANCZOS).convert('RGBA') for s in sizes]
    # Pillow 12.x 保存 ICO 时，会把第一帧的尺寸当作上限，大 size 会被丢弃。
    # 因此必须将最大帧（256x256）放在 save() 的调用者位置，其余帧 append。
    imgs_sorted = sorted(imgs, key=lambda im: im.size[0], reverse=True)
    imgs_sorted[0].save(
        ico_path, format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=imgs_sorted[1:]
    )
    print("wrote", png_path, "and", ico_path)
