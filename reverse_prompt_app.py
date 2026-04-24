#!/usr/bin/env python3
"""图片反推提示词小程序（Tkinter 桌面版）。

功能：
1. 选择本地图片。
2. 调用 OpenAI Responses API（视觉）分析图片并反推中文生图提示词。
3. 结果可复制到剪贴板。

环境变量：
- OPENAI_API_KEY: 必填
- OPENAI_BASE_URL: 可选，默认 https://api.openai.com/v1
- OPENAI_MODEL: 可选，默认 gpt-4.1
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from urllib import error, request

BASE_INSTRUCTION = (
    "反推提示词：\n"
    "分析并反推该图像的AI生图提示词。需涵盖以下要素:\n"
    "风格调性与视觉氛围、拍摄视角或镜头类型、摄影构图技法、场景设定与主要内容、"
    "产品摆放的角度与具体位置(如置于何种物体表面)、场景中各类元素的形态及布局、"
    "物体的材质与质感表现、整体色彩搭配与背景细节描写等。请忽略任何文字排版信息，"
    "充分运用摄影及渲染领域的专业术语进行描述。提示词需符合中文AI绘图工具的解析逻辑，"
    "并最终整合为一段连贯而精准的指令文本。"
)


def image_file_to_data_url(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = "image/png"

    with path.open("rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def call_openai_vision(image_path: Path) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("未检测到 OPENAI_API_KEY。请先设置环境变量。")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1")

    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": BASE_INSTRUCTION},
                    {
                        "type": "input_image",
                        "image_url": image_file_to_data_url(image_path),
                    },
                ],
            }
        ],
    }

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{base_url}/responses",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"API 调用失败（HTTP {e.code}）：{detail}") from e
    except error.URLError as e:
        raise RuntimeError(f"网络请求失败：{e}") from e

    output_text = data.get("output_text")
    if output_text:
        return output_text.strip()

    # 兼容不同响应结构
    output = data.get("output", [])
    chunks: list[str] = []
    for item in output:
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                chunks.append(text)

    if chunks:
        return "\n".join(chunks).strip()

    raise RuntimeError("未从模型响应中解析到文本结果。")


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("图片反推提示词小程序")
        self.root.geometry("820x620")

        self.image_path: Path | None = None

        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=12, pady=10)

        self.path_var = tk.StringVar(value="未选择图片")
        tk.Label(top, textvariable=self.path_var, anchor="w").pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        tk.Button(top, text="选择图片", command=self.choose_image).pack(side=tk.LEFT, padx=6)
        self.generate_btn = tk.Button(top, text="开始反推", command=self.generate)
        self.generate_btn.pack(side=tk.LEFT)

        instruction_frame = tk.LabelFrame(root, text="内置提示词模板")
        instruction_frame.pack(fill=tk.BOTH, padx=12, pady=(0, 10))

        self.instruction = tk.Text(instruction_frame, height=8, wrap=tk.WORD)
        self.instruction.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.instruction.insert("1.0", BASE_INSTRUCTION)

        output_frame = tk.LabelFrame(root, text="反推结果")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        self.output = tk.Text(output_frame, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        bottom = tk.Frame(root)
        bottom.pack(fill=tk.X, padx=12, pady=(0, 12))

        tk.Button(bottom, text="复制结果", command=self.copy_result).pack(side=tk.LEFT)

    def choose_image(self) -> None:
        filename = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp")],
        )
        if not filename:
            return

        self.image_path = Path(filename)
        self.path_var.set(str(self.image_path))

    def generate(self) -> None:
        if not self.image_path:
            messagebox.showwarning("提示", "请先选择图片。")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "正在调用模型，请稍候...\n")

        def worker() -> None:
            try:
                # 允许用户在界面中微调模板后再提交
                global BASE_INSTRUCTION
                BASE_INSTRUCTION = self.instruction.get("1.0", tk.END).strip()
                result = call_openai_vision(self.image_path)
                self.root.after(0, lambda: self.show_result(result))
            except Exception as e:  # noqa: BLE001
                self.root.after(0, lambda: self.show_error(str(e)))
            finally:
                self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def show_result(self, text: str) -> None:
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)

    def show_error(self, text: str) -> None:
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"执行失败：{text}")

    def copy_result(self) -> None:
        content = self.output.get("1.0", tk.END).strip()
        if not content:
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("提示", "结果已复制到剪贴板。")


def main() -> None:
    root = tk.Tk()
    app = App(root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()
