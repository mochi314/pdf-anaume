# -*- coding: utf-8 -*-
import os
from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red
from io import BytesIO

app = Flask(__name__)

# ✅ アップロードフォルダ設定
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

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

        # ✅ PDF を処理
        process_pdf(filepath, output_filepath)

        return send_file(output_filepath, as_attachment=True)

    return "許可されていないファイル形式です", 400

def process_pdf(input_pdf, output_pdf):
    """✅ PDF の白い文字を赤に変換（PyPDF2 + ReportLab で処理）"""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()

        # ✅ 新しい PDF ページを作成
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=page.mediabox[2:])

        # ✅ 赤い文字で書き直し
        c.setFillColor(red)
        c.setFont("Helvetica", 12)  # フォントは変更せず、デフォルトを維持

        if text:
            y_position = page.mediabox[3] - 40  # ページの上部から配置
            for line in text.split("\n"):
                c.drawString(50, y_position, line)  # 50px のマージンを付ける
                y_position -= 15  # 行間を調整

        c.save()
        packet.seek(0)

        # ✅ ReportLab で作成したキャンバスをオーバーレイ
        overlay_pdf = PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])

        # ✅ 書き込み用に追加
        writer.add_page(page)

    # ✅ 出力 PDF を保存
    with open(output_pdf, "wb") as out_pdf:
        writer.write(out_pdf)

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 10000))  # 環境変数 PORT を使用
    app.run(host="0.0.0.0", port=port, debug=False)