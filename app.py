"""拼豆图纸生成器 - Flask 后端"""
import io
import base64
import hashlib
import time
from flask import Flask, request, jsonify, send_file, send_from_directory
from PIL import Image

from processor import process_image, render_color_legend
from colors import MARD_COLORS

app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

# 临时存储生成的图片（内存缓存，最近 20 张）
_image_cache = {}
_cache_order = []
MAX_CACHE = 20


def _cache_put(key: str, data: bytes):
    _image_cache[key] = data
    _cache_order.append(key)
    while len(_cache_order) > MAX_CACHE:
        old = _cache_order.pop(0)
        _image_cache.pop(old, None)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/colors")
def get_colors():
    return jsonify({
        "total": len(MARD_COLORS),
        "colors": [{"code": c.code, "name": c.name, "hex": c.hex} for c in MARD_COLORS],
    })


@app.route("/api/convert", methods=["POST"])
def convert():
    if "image" not in request.files:
        return jsonify({"error": "请上传图片"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "请选择文件"}), 400

    width = min(max(int(request.form.get("width", 58)), 5), 100)
    height = min(max(int(request.form.get("height", 58)), 5), 200)
    dither = request.form.get("dither", "false") == "true"

    try:
        image_bytes = file.read()
        result = process_image(image_bytes, width, height, MARD_COLORS, dither)
        result["total_palette"] = len(MARD_COLORS)

        legend_img = render_color_legend(result["stats"], MARD_COLORS)
        legend_b64 = _img_to_base64(legend_img)
        result["legend_url"] = f"data:image/png;base64,{legend_b64}"

        # 缓存图片数据用于下载
        for key in ["preview_url", "pattern_url", "legend_url"]:
            if key in result and result[key].startswith("data:"):
                b64_data = result[key].split(",", 1)[1]
                img_bytes = base64.b64decode(b64_data)
                cache_key = hashlib.md5(img_bytes[:1024] + str(time.time()).encode()).hexdigest()[:12]
                _cache_put(cache_key, img_bytes)
                result[key.replace("_url", "_key")] = cache_key

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500


@app.route("/api/download/<key>")
def download_image(key):
    """下载缓存中的图片（带正确的 Content-Disposition 头）"""
    data = _image_cache.get(key)
    if not data:
        return jsonify({"error": "图片已过期，请重新生成"}), 404

    filename = request.args.get("name", "拼豆图纸") + ".png"
    return send_file(
        io.BytesIO(data),
        mimetype="image/png",
        as_attachment=True,
        download_name=filename,
    )


def _img_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
