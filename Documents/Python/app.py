# -*- coding: utf-8 -*-
import os
import fitz  # PyMuPDF
from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ✅ アップロードフォルダ設定
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

# ✅ 利用可能なフォントを取得（.ttf のみ）
def get_valid_japanese_font():
    """利用可能なフォントを検索し、.ttf を優先して取得"""
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS ✅ 推奨
        "/Library/Fonts/Osaka.ttf",  # macOS
        "/System/Library/Fonts/Supplemental/Hiragino Sans GB.ttf",  # macOS
        "/System/Library/Fonts/Supplemental/HiraginoSans-W3.ttc",  # macOS ⚠ TTCは不完全
        "C:/Windows/Fonts/MS Gothic.ttf",  # Windows ✅ 推奨
        "C:/Windows/Fonts/YuGothM.ttc",  # Windows ⚠ TTCは不完全
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",  # Linux ✅ 推奨
    ]

    for font in font_candidates:
        if os.path.exists(font):
            print(f"✅ 利用可能なフォントが見つかりました: {font}")
            return font

    print("⚠️ 適切な日本語フォントが見つかりません。デフォルトフォントを使用します。")
    return None  # フォントなしでも実行できるようにする

japanese_font_path = get_valid_japanese_font()

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
    """✅ PDF の白い文字を赤に変換（UTF-8対応）"""
    doc = fitz.open(input_pdf)

    for page in doc:
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("color", 0) == 16777215 and span.get("text", "").strip():
                        text = span["text"]
                        size = span["size"]
                        origin = span.get("origin", (span["bbox"][0], span["bbox"][3]))
                        fontname = span.get("font", "helv")  # ✅ 元のフォントを取得
                        
                        # ✅ UTF-8 デバッグ
                        print(f"処理中: {text.encode('utf-8')} at {origin} | Font: {fontname}")

                        try:
                            # ✅ PyMuPDF が認識できないフォントは Helvetica に置き換え
                            if fontname.startswith("HiraKakuProN"):  
                                print(f"⚠️ '{fontname}' は PyMuPDF でサポートされていません。Helvetica に置き換えます。")
                                fontname = "helv"  

                            # ✅ フォント適用処理
                            if japanese_font_path:
                                page.insert_text(origin, text,
                                                 fontsize=size,
                                                 color=(1, 0, 0),
                                                 fontname=fontname,  # ✅ フォント名を指定
                                                 fontfile=japanese_font_path,  # ✅ 明示的にフォント適用
                                                 overlay=True)
                            else:
                                page.insert_text(origin, text,
                                                 fontsize=size,
                                                 color=(1, 0, 0),
                                                 fontname=fontname,  # ✅ 既存フォントを使用
                                                 overlay=True)
                        except Exception as e:
                            print(f"❌ フォント適用エラー: {e}")

    doc.save(output_pdf)

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 10000))  # 環境変数 PORT を使用
    app.run(host="0.0.0.0", port=port, debug=False)