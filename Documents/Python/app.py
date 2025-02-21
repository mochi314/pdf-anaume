# -*- coding: utf-8 -*-
import os
import fitz  # PyMuPDF
from flask import Flask, request, send_file, render_template, abort
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

# ✅ Render 環境で手動ダウンロードした日本語フォントを適用
def get_valid_japanese_font():
    """手動ダウンロードしたフォントを適用（Render 用）"""
    font_candidates = [
        "static/fonts/ipaexg.ttf",  # IPAex ゴシック
        "static/fonts/ipaexm.ttf",  # IPAex 明朝
        "static/fonts/NotoSansJP-Regular.ttf",  # Noto Sans JP
    ]

    for font in font_candidates:
        if os.path.exists(font):
            print(f"✅ 日本語フォントを適用: {font}")
            return font

    print("⚠️ 指定の日本語フォントが見つかりません。デフォルトフォントを使用します。")
    return None

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
        print("⚠️ ファイルが選択されていません")
        abort(400, "ファイルが選択されていません")
    
    file = request.files["file"]
    if file.filename == "":
        print("⚠️ 空のファイルが選択されました")
        abort(400, "ファイルが選択されていません")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # ✅ 元のファイル名を取得し、"_red.pdf" を追加
        filename_without_ext, file_ext = os.path.splitext(filename)
        output_filepath = os.path.join(app.config["OUTPUT_FOLDER"], f"{filename_without_ext}_red{file_ext}")

        try:
            # ✅ PDF を処理
            process_pdf(filepath, output_filepath)
            return send_file(output_filepath, as_attachment=True)
        except Exception as e:
            print(f"❌ PDF 処理中にエラー発生: {e}")
            abort(500, "PDF 処理中にエラーが発生しました")

    print("⚠️ 許可されていないファイル形式です")
    abort(400, "許可されていないファイル形式です")

def process_pdf(input_pdf, output_pdf):
    """✅ PDF の白い文字を赤に変換（フォント埋め込み修正済み）"""
    try:
        doc = fitz.open(input_pdf)
    except Exception as e:
        print(f"❌ PDF を開く際にエラー: {e}")
        abort(500, "PDF を開く際にエラーが発生しました")

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

                        print(f"🔹 処理中: {text.encode('utf-8')} at {origin}")

                        try:
                            # ✅ フォントを確実に埋め込む
                            if japanese_font_path:
                                font_xref = page.insert_font(fontfile=japanese_font_path, fontname="customfont")
                                page.insert_text(origin, text,
                                                 fontsize=size,
                                                 color=(1, 0, 0),
                                                 fontname="customfont",  # ✅ フォント名を明示
                                                 overlay=True)
                                print(f"✅ {text} を赤字で描画しました at {origin}")
                            else:
                                print("⚠️ 日本語フォントが見つからないため、デフォルトフォントを使用します。")
                                page.insert_text(origin, text,
                                                 fontsize=size,
                                                 color=(1, 0, 0),
                                                 fontname="helv",
                                                 overlay=True)
                        except Exception as e:
                            print(f"❌ フォント適用エラー: {e}")

    try:
        doc.save(output_pdf)
        print(f"✅ 変換完了！保存先: {output_pdf}")
    except Exception as e:
        print(f"❌ PDF 保存中にエラー: {e}")
        abort(500, "PDF 保存中にエラーが発生しました")

if __name__ == "__main__":
    app.run(debug=True)