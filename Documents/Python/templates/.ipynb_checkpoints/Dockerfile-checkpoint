# ✅ Python 3.9 の公式イメージを使う
FROM python:3.9

# ✅ 作業ディレクトリを設定
WORKDIR /app

# ✅ 日本語フォントをインストール（Ubuntu ベース）
RUN apt-get update && apt-get install -y \
    fonts-ipafont \
    && rm -rf /var/lib/apt/lists/*

# ✅ `requirements.txt` をコピー
COPY requirements.txt .

# ✅ Python ライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# ✅ 残りのファイルをコピー
COPY . .

# ✅ Flask アプリを実行
CMD ["python", "app.py"]