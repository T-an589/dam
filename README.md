# 图片反推提示词小程序

一个用 Python + Tkinter 写的桌面小工具：选择一张图片后，调用视觉模型自动“反推”中文 AI 生图提示词。

## 功能

- 内置并可编辑以下模板提示词：

```text
反推提示词：
分析并反推该图像的AI生图提示词。需涵盖以下要素:
风格调性与视觉氛围、拍摄视角或镜头类型、摄影构图技法、场景设定与主要内容、产品摆放的角度与具体位置(如置于何种物体表面)、场景中各类元素的形态及布局、物体的材质与质感表现、整体色彩搭配与背景细节描写等。请忽略任何文字排版信息，充分运用摄影及渲染领域的专业术语进行描述。提示词需符合中文AI绘图工具的解析逻辑，并最终整合为一段连贯而精准的指令文本。
```

- 支持选择常见图片格式（png/jpg/jpeg/webp/bmp）。
- 结果可直接复制。

## 使用方法

1. 准备 Python 3.10+。
2. 设置环境变量：

```bash
export OPENAI_API_KEY="你的API Key"
# 可选：
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4.1"
```

3. 运行：

```bash
python3 reverse_prompt_app.py
```

## 说明

- 程序默认调用 Responses API 的视觉输入能力。
- 若你使用兼容 OpenAI API 的网关，可通过 `OPENAI_BASE_URL` 切换。
