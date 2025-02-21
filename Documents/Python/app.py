# -*- coding: utf-8 -*-
import os
import uuid
from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

app = Flask(__name__)

# ✅ アップロードフォルダ設定
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

# ✅ 日本語フォントの登録
def get_japanese_font():
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS ✅ 推奨
        "/Library/Fonts/Osaka.ttf",  # macOS
        "/System/Library/Fonts/Supplemental/Hiragino Sans GB.ttf",  # macOS
        "C:/Windows/Fonts/MS Gothic.ttf",  # Windows ✅ 推奨
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",  # Linux ✅ 推奨
    ]

    for font in font_candidates:
        if os.path.exists(font):
            print(f"✅ 利用可能なフォントが見つかりました: {font}")
            font_name = "JapaneseFont"
            pdfmetrics.registerFont(TTFont(font_name, font))
            return font_name  # 利用可能なフォント名を返す

    print("⚠️ 日本語フォントが見つかりません。Helvetica を使用します。")
    return "Helvetica"  # フォントがない場合はデフォルトフォント

font_name = get_japanese_font()

# ✅ PDF ファイルの拡張子チェック
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "ファイルが選択されていません", 400
    
    file = request.files["file"]
    if file.filename == "":
        return "ファイルが選択されていません", 400

    if file and allowed_file(file.filename):
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # ✅ 元のファイル名を取得し、"_red.pdf" を追加
        filename_without_ext, file_ext = os.path.splitext(filename)
        output_filepath = os.path.join(app.config["OUTPUT_FOLDER"], f"{filename_without_ext}_red{file_ext}")

        # ✅ PDF を処理
        process_pdf(filepath, output_filepath)

        return send_file(output_filepath, as_attachment=True)

    return "許可されていないファイル形式です", 400

def process_pdf(input_pdf, output_pdf):
    """✅ PDF の白い文字を赤に変換（PyPDF2 + ReportLab）"""
    reader = PdfReader(input_pdf)
    
    for page_num, page in enumerate(reader.pages):
        page_size = (float(page.mediabox.width), float(page.mediabox.height))
        output_canvas = canvas.Canvas(output_pdf, pagesize=page_size)
        output_canvas.setFont(font_name, 12)

        text = page.extract_text()

        if text:
            y_position = page_size[1] - 50  # ページの上端から開始
            for line in text.split("\n"):
                output_canvas.setFillColor(red)  # 文字色を赤に変更
                output_canvas.drawString(50, float(y_position), line)  # 50px のマージン
                y_position -= 14  # 行間を調整

        output_canvas.showPage()  # ✅ 新しいページを追加
        output_canvas.save()  # PDF を保存

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 10000))  # 環境変数 PORT を使用
    app.run(host="0.0.0.0", port=port, debug=False)