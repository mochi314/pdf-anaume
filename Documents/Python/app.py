# -*- coding: utf-8 -*-
import os
from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
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

# ✅ 利用可能な日本語フォントを取得
def get_japanese_font():
    """Render（Linux環境）で利用できるフォントを選択"""
    font_candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # ✅ Linux環境の推奨フォント
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # ✅ バックアップ用（日本語対応なし）
    ]

    for font in font_candidates:
        if os.path.exists(font):
            print(f"✅ 利用可能なフォントが見つかりました: {font}")
            return font

    print("⚠️ 適切なフォントが見つかりません。デフォルトの Helvetica を使用します。")
    return None  # フォントなしでも実行できるようにする

JAPANESE_FONT_PATH = get_japanese_font()

# ✅ フォント登録
if JAPANESE_FONT_PATH:
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

        # ✅ PDF を処理
        process_pdf(filepath, output_filepath)

        return send_file(output_filepath, as_attachment=True)

    return "許可されていないファイル形式です", 400

def process_pdf(input_pdf, output_pdf):
    """✅ PDF の白い文字を赤に変換（PyPDF2 + ReportLab 版）"""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            # ✅ ReportLab を使って新しいPDFを作成
            temp_pdf_path = f"{OUTPUT_FOLDER}/temp_page_{i}.pdf"
            c = canvas.Canvas(temp_pdf_path, pagesize=letter)

            if JAPANESE_FONT_PATH:
                c.setFont("CustomFont", 12)
            else:
                c.setFont("Helvetica", 12)  # フォントがない場合はデフォルトを使用

            # ✅ 赤い色でテキストを描画
            c.setFillColorRGB(1, 0, 0)  # 赤
            c.drawString(100, 750, text)  # 適当な位置にテキストを描画
            c.save()

            # ✅ PyPDF2 でオリジナルのページと合成
            temp_reader = PdfReader(temp_pdf_path)
            page.merge_page(temp_reader.pages[0])

        writer.add_page(page)

    # ✅ 変換後のPDFを保存
    with open(output_pdf, "wb") as output_file:
        writer.write(output_file)

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 10000))  # 環境変数 PORT を使用
    app.run(host="0.0.0.0", port=port, debug=False)