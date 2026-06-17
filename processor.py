"""图片处理核心 - 像素化 + 拼豆颜色映射"""
import io
import math
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from colors import BeadColor


def find_nearest_color(r: int, g: int, b: int, palette: list[BeadColor]) -> BeadColor:
    """找最近的拼豆颜色 (加权欧氏距离)"""
    min_dist = float("inf")
    nearest = palette[0]
    for c in palette:
        dist = math.sqrt(2 * (r - c.r) ** 2 + 4 * (g - c.g) ** 2 + 3 * (b - c.b) ** 2)
        if dist < min_dist:
            min_dist = dist
            nearest = c
    return nearest


def process_image(
    image_bytes: bytes,
    width: int,
    height: int,
    palette: list[BeadColor],
    dither: bool = False,
) -> dict:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    orig_w, orig_h = img.size
    aspect = orig_w / orig_h
    target_aspect = width / height

    if aspect > target_aspect:
        new_w = width
        new_h = max(1, round(width / aspect))
    else:
        new_h = height
        new_w = max(1, round(height * aspect))

    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    if dither:
        img_resized = _floyd_steinberg_dither(img_resized, palette)

    pixels = np.array(img_resized)
    grid, stats = [], {}

    for y in range(new_h):
        row = []
        for x in range(new_w):
            r, g, b = int(pixels[y, x, 0]), int(pixels[y, x, 1]), int(pixels[y, x, 2])
            nearest = find_nearest_color(r, g, b, palette)
            row.append({"code": nearest.code, "name": nearest.name, "hex": nearest.hex,
                        "r": nearest.r, "g": nearest.g, "b": nearest.b})
            if nearest.code not in stats:
                stats[nearest.code] = {"name": nearest.name, "hex": nearest.hex, "count": 0}
            stats[nearest.code]["count"] += 1
        grid.append(row)

    stats = dict(sorted(stats.items(), key=lambda x: -x[1]["count"]))
    total_beads = sum(s["count"] for s in stats.values())

    preview_img = _render_preview(grid, new_w, new_h, cell_size=max(10, min(30, 800 // max(new_w, 1))))
    pattern_img = _render_pattern(grid, new_w, new_h)

    import base64
    return {
        "grid": grid, "width": new_w, "height": new_h,
        "stats": stats, "total_beads": total_beads, "color_count": len(stats),
        "preview_url": f"data:image/png;base64,{base64.b64encode(_to_bytes(preview_img)).decode()}",
        "pattern_url": f"data:image/png;base64,{base64.b64encode(_to_bytes(pattern_img)).decode()}",
    }


def _floyd_steinberg_dither(img: Image.Image, palette: list[BeadColor]) -> Image.Image:
    pixels = np.array(img, dtype=float)
    h, w = pixels.shape[:2]
    for y in range(h):
        for x in range(w):
            old = pixels[y, x]
            n = find_nearest_color(int(old[0]), int(old[1]), int(old[2]), palette)
            new = np.array([n.r, n.g, n.b], dtype=float)
            pixels[y, x] = new
            err = old - new
            if x + 1 < w: pixels[y, x + 1] += err * 7 / 16
            if y + 1 < h:
                if x - 1 >= 0: pixels[y + 1, x - 1] += err * 3 / 16
                pixels[y + 1, x] += err * 5 / 16
                if x + 1 < w: pixels[y + 1, x + 1] += err * 1 / 16
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))


def _render_preview(grid: list, w: int, h: int, cell_size: int = 20) -> Image.Image:
    """预览图：纯色块"""
    img = Image.new("RGB", (w * cell_size, h * cell_size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            x0, y0 = x * cell_size, y * cell_size
            draw.rectangle([x0, y0, x0 + cell_size - 1, y0 + cell_size - 1],
                           fill=(cell["r"], cell["g"], cell["b"]))
    return img


def _render_pattern(grid: list, w: int, h: int) -> Image.Image:
    """图纸：带网格线和色号编号（自适应高清）"""
    # 自适应格子大小：保证图纸总宽度在 4000~5000px 之间
    TARGET_W = 4500
    margin_l = 140
    margin_t = 140
    cell_size = max(28, min(120, (TARGET_W - margin_l) // max(w, 1)))

    img_w = margin_l + w * cell_size + 4
    img_h = margin_t + h * cell_size + 4

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 字体：根据格子大小自适应
    font_size = max(16, cell_size // 3)
    font_size_sm = max(14, cell_size // 5)
    font, font_sm = _get_fonts(font_size, font_size_sm)

    # ---- 列号 (顶部) ----
    for x in range(w):
        cx = margin_l + x * cell_size + cell_size // 2
        draw.text((cx, margin_t // 2), str(x + 1), fill=(120, 120, 120), font=font_sm, anchor="mm")

    # ---- 行号 (左侧) ----
    for y in range(h):
        cy = margin_t + y * cell_size + cell_size // 2
        draw.text((margin_l // 2, cy), str(y + 1), fill=(120, 120, 120), font=font_sm, anchor="mm")

    # ---- 单元格 ----
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            x0 = margin_l + x * cell_size
            y0 = margin_t + y * cell_size
            color = (cell["r"], cell["g"], cell["b"])

            # 填充色块
            draw.rectangle([x0, y0, x0 + cell_size - 1, y0 + cell_size - 1], fill=color)

            # 文字颜色：深色背景用白字，浅色背景用黑字
            lum = 0.299 * cell["r"] + 0.587 * cell["g"] + 0.114 * cell["b"]
            txt_color = (255, 255, 255) if lum < 140 else (0, 0, 0)

            # 色号文字
            cx = x0 + cell_size // 2
            cy = y0 + cell_size // 2
            draw.text((cx, cy), cell["code"], fill=txt_color, font=font, anchor="mm")

    # ---- 网格线 ----
    grid_color = (180, 180, 180)
    line_w = max(1, cell_size // 25)
    for x in range(w + 1):
        lx = margin_l + x * cell_size
        draw.line([(lx, margin_t), (lx, margin_t + h * cell_size)], fill=grid_color, width=line_w)
    for y in range(h + 1):
        ly = margin_t + y * cell_size
        draw.line([(margin_l, ly), (margin_l + w * cell_size, ly)], fill=grid_color, width=line_w)

    # ---- 外边框 ----
    draw.rectangle(
        [margin_l, margin_t, margin_l + w * cell_size, margin_t + h * cell_size],
        outline=(80, 80, 80), width=max(2, cell_size // 20)
    )

    return img


def _get_fonts(size: int, size_sm: int):
    """加载字体"""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font = font_sm = None
    for path in candidates:
        try:
            font = ImageFont.truetype(path, size)
            font_sm = ImageFont.truetype(path, size_sm)
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()
        font_sm = font
    return font, font_sm


def _to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_color_legend(stats: dict, palette: list[BeadColor]) -> Image.Image:
    """颜色图例"""
    cell_h = 48
    cols = 2
    rows_per_col = math.ceil(len(stats) / cols)
    img_w = 600 * cols
    img_h = 80 + rows_per_col * cell_h

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    font, font_sm = _get_fonts(18, 16)
    draw.text((img_w // 2, 40), "颜色用量统计", fill=(50, 50, 50), font=font, anchor="mm")

    color_map = {c.code: c for c in palette}
    for i, (code, info) in enumerate(stats.items()):
        col = i // rows_per_col
        row = i % rows_per_col
        x = 30 + col * 600
        y = 70 + row * cell_h

        c = color_map.get(code)
        if c:
            draw.rectangle([x, y + 4, x + 36, y + cell_h - 6], fill=(c.r, c.g, c.b), outline=(180, 180, 180))
        draw.text((x + 44, y + cell_h // 2), f"{code} {info['name']}", fill=(60, 60, 60), font=font_sm, anchor="lm")
        draw.text((x + 420, y + cell_h // 2), f"x {info['count']}", fill=(30, 30, 30), font=font_sm, anchor="lm")

    return img
