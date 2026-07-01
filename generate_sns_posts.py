import os
import re
import random
import sys
from article_generator import ArticleGenerator

# 設定
YUI_UNIVERSE_DIR = "/Users/calro/Desktop/yui-universe"
WORKSPACE_DIR = "/Users/calro/Downloads/x-auto"
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output")
USED_ARTICLES_FILE = os.path.join(WORKSPACE_DIR, "used_articles.txt")

def load_used_articles() -> set:
    if os.path.exists(USED_ARTICLES_FILE):
        with open(USED_ARTICLES_FILE, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    return set()

def save_used_articles(used_set: set):
    with open(USED_ARTICLES_FILE, "w", encoding="utf-8") as f:
        for item in sorted(used_set):
            f.write(f"{item}\n")

def extract_meta_info(file_path: str) -> tuple:
    title = ""
    description = ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # titleの抽出
        title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            # パイプやサイト名などの余計な部分をカット
            title = re.split(r"[|【]", title)[0].strip()

        # descriptionの抽出
        desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', content, re.IGNORECASE)
        if not desc_match:
            desc_match = re.search(r'<meta[^>]*content="([^"]*)"[^>]*name="description"', content, re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip()
            # 長すぎるディスクリプションは前半だけ使う
            if len(description) > 100:
                description = description[:100] + "..."
    except Exception as e:
        print(f"Error reading metadata from {file_path}: {e}")
        
    return title, description

def generate_post_for_article(generator: ArticleGenerator, file_name: str, title: str, description: str) -> str:
    article_name = file_name.replace(".html", "")
    link = f"yui-yuto.com/{article_name}"
    
    system_instruction = (
        "คุณเป็นครูสอนภาษาญี่ปุ่นและผู้เชี่ยวชาญด้าน SNS ให้เขียนโพสต์แนะนำบทความสำหรับคนไทยที่ต้องการเรียนภาษาญี่ปุ่นหรือทำงานในญี่ปุ่น เพื่อโพสต์ลง X (Twitter)"
    )
    
    prompt = (
        f"จากข้อมูลบทความต่อไปนี้:\n"
        f"ชื่อบทความ (Title): {title}\n"
        f"คำอธิบาย (Description): {description}\n\n"
        f"กรุณาสร้างข้อความสำหรับโพสต์ลง X (Twitter) โดยมีเงื่อนไขสำคัญดังนี้:\n"
        f"1. อธิบายว่าผู้ใช้อ่านบทความนี้แล้วจะได้เรียนรู้อะไรบ้าง เป็นภาษาไทยที่น่าสนใจและดึงดูดใจ (สไตล์การเขียนแบบ X/Twitter ที่มีโอกาสเป็นไวรัล)\n"
        f"2. ความยาวของข้อความอธิบายต้องไม่เกิน 90 ตัวอักษร (ไม่รวมลิงก์)\n"
        f"3. ห้ามใช้ตัวหนา Markdown (**)\n"
        f"4. ห้ามใส่เครื่องหมายคำพูด (เช่น \" หรือ ') รอบข้อความทั้งหมด\n"
        f"5. ข้อความสุดท้ายต้องลงท้ายด้วยลิงก์นี้: {link}\n"
        f"6. เมื่อรวมข้อความทั้งหมดแล้ว (รวมข้อความอธิบาย, การเว้นบรรทัด, และลิงก์) ความยาวรวมต้องไม่เกิน 140 ตัวอักษรเด็ดขาด! (สำคัญมาก)\n\n"
        f"รูปแบบผลลัพธ์ที่ต้องการ (ให้มีขึ้นบรรทัดใหม่ตามตัวอย่างนี้ โดยไม่ต้องมีเครื่องหมายคำพูดปิดหัวท้าย):\n"
        f"[ข้อความโปรโมทบรรทัดที่ 1]\n"
        f"[ข้อความโปรโมทบรรทัดที่ 2]\n"
        f"{link}"
    )

    max_retries = 3
    for attempt in range(max_retries):
        print(f"Generating post for {file_name} (Attempt {attempt+1}/{max_retries})...")
        generated = generator.generate_text(prompt, system_instruction)
        if generated:
            generated = generated.strip().strip('"').strip("'")
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

    # リトライしても140文字を超えてしまった場合の最終手段（強制トリミング）
    print("Warning: Forced to truncate the generated post to fit 140 characters.")
    # リンクの長さを引いた残りの文字数に収まるように説明部分をカット
    link_part = f"\n{link}"
    max_desc_len = 140 - len(link_part)
    truncated = generated[:max_desc_len]
    return f"{truncated}{link_part}"

def main():
    print("Starting X Post Content Generator...")
    
    if not os.path.exists(YUI_UNIVERSE_DIR):
        print(f"Error: Directory {YUI_UNIVERSE_DIR} does not exist.")
        sys.exit(1)
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 対象のHTMLファイルをスキャン (th-で始まるHTMLファイル)
    all_files = [f for f in os.listdir(YUI_UNIVERSE_DIR) if f.startswith("th-") and f.endswith(".html")]
    print(f"Found {len(all_files)} total Thai articles.")
    
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
        file_path = os.path.join(YUI_UNIVERSE_DIR, file_name)
        title, description = extract_meta_info(file_path)
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
