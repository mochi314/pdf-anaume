# -*- coding: utf-8 -*-
import os
from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# ✅ アップロードフォルダ設定
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

# ✅ 日本語フォントを登録 (フォントパスを環境に合わせて変更)
JAPANESE_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"  # macOS
# JAPANESE_FONT_PATH = "C:/Windows/Fonts/msgothic.ttc"  # Windows
# JAPANESE_FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"  # Linux

pdfmetrics.registerFont(TTFont("CustomFont", JAPANESE_FONT_PATH))

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
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # ✅ 元のファイル名を取得し、"_red.pdf" を追加
        filename_without_ext, file_ext = os.path.splitext(filename)
        output_filepath = os.path.join(app.config["OUTPUT_FOLDER"], f"{filename_without_ext}_red{file_ext}")

        # ✅ PDF を作成
        create_pdf_with_red_text(filepath, output_filepath)

        return send_file(output_filepath, as_attachment=True)

    return "許可されていないファイル形式です", 400

def create_pdf_with_red_text(input_text_file, output_pdf):
    """✅ reportlab を使って日本語PDFを作成し、白い文字を赤に変換"""
    c = canvas.Canvas(output_pdf, pagesize=letter)
    c.setFont("CustomFont", 16)

    # ✅ 既存のPDFを開く代わりに、アップロードされたPDFのテキストを読み込む
    with open(input_text_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    y_position = 750  # ページ上部から開始
    for line in lines:
        line = line.strip()
        if line:  # 空行でなければ描画
            c.setFillColorRGB(1, 0, 0)  # 🔴 赤い文字に変換
            c.drawString(100, y_position, line)  # 日本語テキストを描画
            y_position -= 20  # 次の行に移動

    c.save()
    print(f"✅ PDF を生成しました: {output_pdf}")

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 10000))  # 環境変数 PORT を使用
    app.run(host="0.0.0.0", port=port, debug=False)