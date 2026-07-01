import os
import re
import random
import sys
import requests
from article_generator import ArticleGenerator

# 設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = SCRIPT_DIR
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output")
USED_ARTICLES_FILE = os.path.join(WORKSPACE_DIR, "used_articles.txt")
ARTICLE_LIST_FILE = os.path.join(WORKSPACE_DIR, "article_list.json")

# ローカルデバッグ用
LOCAL_YUI_UNIVERSE_DIR = "/Users/calro/Desktop/yui-universe"

def load_used_articles() -> set:
    if os.path.exists(USED_ARTICLES_FILE):
        with open(USED_ARTICLES_FILE, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    return set()

def save_used_articles(used_set: set):
    with open(USED_ARTICLES_FILE, "w", encoding="utf-8") as f:
        for item in sorted(used_set):
            f.write(f"{item}\n")

import json

def update_article_list(files: list):
    """ローカルデバッグ時にファイル一覧をjsonに保存する"""
    try:
        with open(ARTICLE_LIST_FILE, "w", encoding="utf-8") as f:
            json.dump(files, f, ensure_ascii=False, indent=2)
        print(f"Updated article_list.json with {len(files)} articles.")
    except Exception as e:
        print(f"Failed to update article_list.json: {e}")

def load_article_list() -> list:
    """保存されたファイル一覧を読み込む"""
    if os.path.exists(ARTICLE_LIST_FILE):
        try:
            with open(ARTICLE_LIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading article_list.json: {e}")
    return []

def extract_meta_info(file_name: str) -> tuple:
    title = ""
    description = ""
    content = ""
    
    # 1. ローカルファイルが存在する場合はローカルから読み込む
    local_path = os.path.join(LOCAL_YUI_UNIVERSE_DIR, file_name)
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"Read metadata from local file: {file_name}")
        except Exception as e:
            print(f"Error reading local file {file_name}: {e}")
    else:
        # 2. 存在しない場合（GitHub Actions環境など）は公開ウェブサイトからスクレイピング
        article_name = file_name.replace(".html", "")
        url = f"https://yui-yuto.com/{article_name}"
        try:
            print(f"Fetching metadata from public URL: {url}")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                content = resp.text
            else:
                print(f"Failed to fetch URL (Status {resp.status_code}): {url}")
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")

    if content:
        try:
            # titleの抽出
            title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                title = re.split(r"[|【]", title)[0].strip()

            # descriptionの抽出
            desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', content, re.IGNORECASE)
            if not desc_match:
                desc_match = re.search(r'<meta[^>]*content="([^"]*)"[^>]*name="description"', content, re.IGNORECASE)
            if desc_match:
                description = desc_match.group(1).strip()
                if len(description) > 100:
                    description = description[:100] + "..."
        except Exception as e:
            print(f"Error parsing meta content: {e}")
        
    return title, description

def generate_post_for_article(generator: ArticleGenerator, file_name: str, title: str, description: str) -> str:
    article_name = file_name.replace(".html", "")
    link = f"yui-yuto.com/{article_name}"
    
    system_instruction = (
        "คุณเป็นครูสอนภาษาญี่ปุ่นและผู้เชี่ยวชาญด้าน SNS ที่เก่งมากในการเขียนคำโปรยดึงดูดใจ ให้เขียนโพสต์แนะนำบทความสำหรับคนไทยเพื่อโพสต์ลง X (Twitter)"
    )
    
    # 無料API（PollinationsやGPT-4o-mini）が理解しやすいようにシンプルで強力なプロンプトにする
    prompt = (
        f"เขียนข้อความสั้นๆ สำหรับโพสต์ลง X (Twitter) เพื่อโปรโมทบทความนี้:\n"
        f"หัวข้อบทความ: {title}\n"
        f"รายละเอียดบทความ: {description}\n\n"
        f"เงื่อนไขบังคับ:\n"
        f"1. สรุป 'ประโยชน์/สิ่งที่จะได้เรียนรู้' จากบทความนี้ให้คนอ่านอยากคลิก (สไตล์ดึงดูดใจคนอ่านสูง)\n"
        f"2. ข้อความทั้งหมด (รวมลิงก์ด้านล่างนี้) ต้องยาวไม่เกิน 140 ตัวอักษรเด็ดขาด!\n"
        f"3. บรรทัดสุดท้ายต้องลงท้ายด้วยลิงก์นี้เท่านั้น: {link}\n"
        f"4. ห้ามใส่เครื่องหมายคำพูดคำพูดปิดหัวท้าย\n\n"
        f"ตัวอย่างผลลัพธ์ที่ต้องการ:\n"
        f"อยากทำพาร์ทไทม์เซเว่นญี่ปุ่น?🏪 สอนภาษาญี่ปุ่นหน้าแคชเชียร์ ประโยคคุยกับลูกค้าและศัพท์ที่ใช้จริง อ่านจบทำงานได้เลย👇\n"
        f"{link}"
    )

    max_retries = 3
    generated = None
    for attempt in range(max_retries):
        print(f"Generating post for {file_name} (Attempt {attempt+1}/{max_retries})...")
        generated = generator.generate_text(prompt, system_instruction)
        if generated:
            generated = generated.strip().strip('"').strip("'")
            
            # 異常な長文（例: 250文字以上）はAPIの誤作動（プロンプトの鸚鵡返しなど）として弾く
            if len(generated) > 250:
                print(f"Generated text is abnormally long ({len(generated)} chars). Retrying...")
                prompt += "\n\n【เตือนความจำ】ข้อความยาวเกินไป! กรุณาตอบให้สั้นลงอย่างมาก"
                continue

            # リンクが最後に入っているか確認し、無ければ付与
            if link not in generated:
                generated = f"{generated}\n{link}"
            
            # 全体の文字数チェック
            total_len = len(generated)
            if total_len <= 140:
                return generated
            else:
                print(f"Generated text too long ({total_len} chars). Retrying with stricter limit...")
                prompt += "\n\n【เตือนความจำ】ข้อความยาวเกินไป! กรุณาเขียนให้สั้นลงอีกเพื่อให้รวมลิงก์แล้วไม่เกิน 140 ตัวอักษร"

    # API呼び出しが全て失敗した、または適切な長さで生成できなかった場合はエラーを投げる
    if not generated or len(generated) < 20:
        raise RuntimeError(f"Failed to generate a valid post content for {file_name} due to API issues.")

    # リトライしても140文字を超えてしまった場合の最終手段（強制トリミング）
    print("Warning: Forced to truncate the generated post to fit 140 characters.")
    # リンクの長さを引いた残りの文字数に収まるように説明部分をカット
    link_part = f"\n{link}"
    max_desc_len = 140 - len(link_part)
    truncated = generated[:max_desc_len]
    return f"{truncated}{link_part}"

def main():
    print("Starting X Post Content Generator...")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_files = []
    # 1. ローカルフォルダが存在する場合はスキャンし、リストを更新
    if os.path.exists(LOCAL_YUI_UNIVERSE_DIR):
        all_files = [f for f in os.listdir(LOCAL_YUI_UNIVERSE_DIR) if f.startswith("th-") and f.endswith(".html")]
        print(f"Scanned {len(all_files)} total Thai articles from local directory.")
        update_article_list(all_files)
    else:
        # 2. 存在しない場合（GitHub Actions環境）は保存されたリストから読み込み
        all_files = load_article_list()
        print(f"Loaded {len(all_files)} total Thai articles from article_list.json.")
        
    if not all_files:
        print("No articles found to process. Please run locally first to generate article_list.json.")
        sys.exit(1)
        
    used_articles = load_used_articles()
    print(f"Loaded {len(used_articles)} used articles.")
    
    # 未使用の記事をフィルタリング
    available_files = [f for f in all_files if f not in used_articles]
    print(f"Available articles for selection: {len(available_files)}")
    
    # 候補が足りない場合は使用済みリストをリセット
    if len(available_files) < 3:
        print("Not enough available articles. Resetting the used articles list...")
        used_articles = set()
        available_files = all_files
        print(f"Reset complete. Available articles: {len(available_files)}")
        
    if not available_files:
        print("No articles found to process.")
        sys.exit(1)
        
    # ランダムに3つの記事を選択
    selected_files = random.sample(available_files, min(3, len(available_files)))
    print(f"Selected articles: {selected_files}")
    
    generator = ArticleGenerator()
    
    for file_name in selected_files:
        title, description = extract_meta_info(file_name)
        print(f"Article: {file_name} | Title: {title} | Desc: {description}")
        
        post_content = generate_post_for_article(generator, file_name, title, description)
        
        # 出力テキストの作成
        output_content = (
            f"file_name\n"
            f"{file_name}\n"
            f"sns_post\n\n"
            f"{post_content}\n"
        )
        
        article_name = file_name.replace(".html", "")
        output_file_path = os.path.join(OUTPUT_DIR, f"{article_name}.txt")
        
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"Saved generated post to: {output_file_path}")
        
        # 使用済みリストに追記
        used_articles.add(file_name)
        
    save_used_articles(used_articles)
    print("Process completed successfully.")

if __name__ == "__main__":
    main()
