# 🎨 拼豆图纸生成器

> 上传图片，一键生成拼豆像素画图纸。支持 Mard 221 色官方色卡，自适应高清分辨率，手机/桌面全平台可用。

![License](https://img.shields.io/badge/license-MIT-blue)
![Docker](https://img.shields.io/badge/docker-ready-2496ED)
![Python](https://img.shields.io/badge/python-3.12-3776AB)
![Colors](https://img.shields.io/badge/colors-221-brightgreen)

## ✨ 功能特性

### 🖼️ 图片转图纸
- 上传任意图片（JPG/PNG/GIF/WebP，最大 20MB）
- 智能像素化 + 颜色映射（加权欧氏距离，人眼感知优化）
- 支持 Floyd-Steinberg 抖动算法，色彩过渡更细腻
- 自动生成预览图、带色号的高清图纸、颜色统计、色卡图例

### 🎨 Mard 221 色官方色卡
- 数据来源：[pd.anqstar.com/colors](https://pd.anqstar.com/colors)
- 9 个色系，221 种颜色，HEX 与 RGB 编码完整收录

| 色系 | 色号 | 数量 | 说明 |
|------|------|------|------|
| A 系 | A1-A26 | 26 色 | 黄橙系 |
| B 系 | B1-B32 | 32 色 | 绿系 |
| C 系 | C1-C29 | 29 色 | 蓝系 |
| D 系 | D1-D26 | 26 色 | 紫系 |
| E 系 | E1-E24 | 24 色 | 粉系 |
| F 系 | F1-F25 | 25 色 | 红系 |
| G 系 | G1-G21 | 21 色 | 棕橙系 |
| H 系 | H1-H23 | 23 色 | 灰黑白系 |
| M 系 | M1-M15 | 15 色 | 特殊色 |

### 📐 自定义画板
- 宽度 5~100，高度 5~200，滑块 + 数字输入双模式
- 快捷尺寸按钮：29×29 / 58×29 / 58×58 / 100×58 / 100×100
- 自适应高清分辨率：不管多大尺寸，图纸总宽保持 ~4500px

### 💾 导出与保存
- **Web Share API**：手机端原生分享菜单，可直接「存储到相册」
- **Blob URL 下载**：兼容所有浏览器
- **新窗口打开**：兜底方案，长按图片保存
- 支持单独下载预览图、图纸、颜色图例

### 📱 移动端适配
- 响应式布局，手机端单列显示
- 底部固定「生成拼豆图纸」按钮
- 卡片可折叠，节省屏幕空间
- 色块 hover/触控显示色号和名称

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 + Flask + Gunicorn |
| 图片处理 | Pillow + NumPy |
| 前端 | 原生 HTML/CSS/JS（无框架依赖） |
| 容器 | Docker + Docker Compose |
| 字体 | DejaVu Sans（清晰渲染） |

## 🚀 快速开始

### Docker 部署（推荐）

```bash
# 克隆仓库
git clone https://github.com/LargePin/perler.git
cd perler

# 构建并启动
docker compose up -d --build

# 访问
open http://localhost:5050
```

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py

# 或使用 Gunicorn 生产模式
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

## 📁 项目结构

```
perler/
├── app.py              # Flask 后端（API 路由 + 图片缓存）
├── processor.py        # 图片处理核心
│   ├── find_nearest_color()    # 颜色匹配（加权欧氏距离）
│   ├── process_image()         # 主流程：缩放→映射→渲染
│   ├── _floyd_steinberg_dither()  # 抖动算法
│   ├── _render_preview()       # 预览图渲染
│   ├── _render_pattern()       # 高清图纸渲染（自适应分辨率）
│   └── render_color_legend()   # 颜色图例渲染
├── colors.py           # Mard 221 色色卡数据
├── static/
│   └── index.html      # 前端页面（响应式 + 移动端适配）
├── Dockerfile          # Docker 镜像定义
├── docker-compose.yml  # 容器编排
├── requirements.txt    # Python 依赖
└── .dockerignore
```

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 前端页面 |
| `GET` | `/api/colors` | 获取 221 色色卡数据 |
| `POST` | `/api/convert` | 上传图片生成图纸 |

### POST /api/convert

**请求参数（multipart/form-data）：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | File | ✅ | 图片文件 |
| `width` | int | ❌ | 画板宽度（5-100，默认 58） |
| `height` | int | ❌ | 画板高度（5-200，默认 58） |
| `dither` | bool | ❌ | 是否启用抖动（默认 false） |

**响应示例：**

```json
{
  "width": 58,
  "height": 58,
  "color_count": 12,
  "total_beads": 3364,
  "total_palette": 221,
  "preview_url": "data:image/png;base64,...",
  "pattern_url": "data:image/png;base64,...",
  "legend_url": "data:image/png;base64,...",
  "stats": {
    "A1": {"name": "#FAF4C8", "hex": "#FAF4C8", "count": 450},
    "F2": {"name": "#FC3D46", "hex": "#FC3D46", "count": 320}
  }
}
```

## 🔧 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PYTHONUNBUFFERED` | `1` | Python 输出不缓冲 |

### 端口配置

修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "5050:5000"  # 左边是宿主机端口，右边是容器端口
```

## 📝 更新日志

### v1.0.0 (2026-06-17)
- ✅ Mard 221 色官方色卡完整收录
- ✅ 自适应高清分辨率渲染
- ✅ 移动端响应式适配
- ✅ 保存到相册功能（Web Share API + Blob 下载）
- ✅ 画板尺寸滑块控制
- ✅ Docker 容器化部署

## 📄 License

MIT License

## 🙏 致谢

- [Mard 拼豆](https://pd.anqstar.com) - 官方色卡数据
- [Pillow](https://pillow.readthedocs.io/) - Python 图像处理库
- [Flask](https://flask.palletsprojects.com/) - Python Web 框架
