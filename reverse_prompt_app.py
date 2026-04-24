#!/usr/bin/env python3
"""图片反推提示词小程序（CLI 版）

用法示例：
  export OPENAI_API_KEY="..."
  python reverse_prompt_app.py --image ./demo.jpg

如果只想查看内置反推提示词模板：
  python reverse_prompt_app.py --print-template
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import os
import sys
from pathlib import Path

DEFAULT_REVERSE_PROMPT = (
    "反推提示词：\n"
    "分析并反推该图像的AI生图提示词。需涵盖以下要素:\n"
    "风格调性与视觉氛围、拍摄视角或镜头类型、摄影构图技法、场景设定与主要内容、"
    "产品摆放的角度与具体位置(如置于何种物体表面)、场景中各类元素的形态及布局、"
    "物体的材质与质感表现、整体色彩搭配与背景细节描写等。"
    "请忽略任何文字排版信息，充分运用摄影及渲染领域的专业术语进行描述。"
    "提示词需符合中文AI绘图工具的解析逻辑，并最终整合为一段连贯而精准的指令文本。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="图片反推提示词小程序")
    parser.add_argument("--image", type=Path, help="图片路径（jpg/png/webp 等）")
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="用于图像分析的模型名称，默认 gpt-4.1-mini",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_REVERSE_PROMPT,
        help="可覆盖内置反推提示词模板",
    )
    parser.add_argument(
        "--print-template",
        action="store_true",
        help="仅打印内置反推提示词模板，不调用模型",
    )
    return parser.parse_args()


def image_to_data_url(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(image_path.name)
    if not mime_type:
        mime_type = "image/jpeg"

    raw = image_path.read_bytes()
    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def run() -> int:
    args = parse_args()

    if args.print_template:
        print(DEFAULT_REVERSE_PROMPT)
        return 0

    if not args.image:
        print("错误：请使用 --image 指定图片路径，或使用 --print-template。", file=sys.stderr)
        return 2

    if not args.image.exists() or not args.image.is_file():
        print(f"错误：图片不存在或不是文件：{args.image}", file=sys.stderr)
        return 2

    if not os.getenv("OPENAI_API_KEY"):
        print("错误：未检测到 OPENAI_API_KEY 环境变量。", file=sys.stderr)
        return 2

    from openai import OpenAI

    client = OpenAI()
    data_url = image_to_data_url(args.image)

    response = client.responses.create(
        model=args.model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": args.prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
    )

    print("\n=== 反推提示词结果 ===\n")
    print(response.output_text.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
