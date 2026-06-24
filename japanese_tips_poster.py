import os
import sys
import json
import re
import requests
from article_generator import ArticleGenerator

def main():
    print("Starting Japanese Tips Generator...")
    
    # 履歴データの読み込み
    history_file = "history.json"
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception as e:
            print(f"Error loading history: {e}")
            history = []
            
    print(f"Current history ({len(history)} items): {history}")
    
    generator = ArticleGenerator()
    
    system_instruction = (
        "คุณเป็นครูสอนภาษาญี่ปุ่นให้กับคนไทยที่ไม่มีพื้นฐานเลย (ระดับ N5) "
        "ให้สร้างโพสต์แนะนำคำศัพท์หรือประโยคสั้นๆ 1 ข้อความสำหรับลง X (Twitter) "
        "โดยเน้นความสั้นกระชับมากที่สุด ห้ามเกริ่นนำหรือทักทายใดๆ ทั้งสิ้น\n"
        "【กฎสำคัญที่สุด】ห้ามเลือกคำศัพท์ ไวยากรณ์ หรือหัวข้อที่ซ้ำกับคำในรายการที่เคยใช้ไปแล้วด้านล่างนี้เด็ดขาด! ต้องเลือกเรื่องใหม่ทุกครั้ง"
    )
    
    history_str = ", ".join(history) if history else "ไม่มี (นี่เป็นครั้งแรก)"
    
    prompt = (
        "สร้างเนื้อหาแนะนำภาษาญี่ปุ่นสำหรับคนไทย (ระดับ N5) 1 โพสต์ เพื่อโพสต์ลง X (Twitter)\n\n"
        "【รายการคำศัพท์/หัวข้อที่เคยใช้ไปแล้ว (ห้ามซ้ำเด็ดขาด!)】\n"
        f"{history_str}\n\n"
        "【เงื่อนไขสำคัญ - ต้องสั้นกระชับสุดๆ เพื่อให้รวมลิงก์แล้วไม่เกิน 140 ตัวอักษร】\n"
        "1. ห้ามมีคำอธิบายความหมายที่ยาวเกินไป ให้ใช้รูปแบบสั้นตามตัวอย่างเท่านั้น\n"
        "2. เลือกหัวข้อระดับเริ่มต้นมากๆ ที่ไม่ซ้ำกับรายการด้านบน (คำศัพท์เดี่ยวๆ หรือวลีสั้นๆ)\n"
        "3. ห้ามใช้ตัวหนา Markdown (ห้ามใส่ **)\n"
        "4. ลงท้ายด้วยแฮชแท็ก #เรียนภาษาญี่ปุ่น #ภาษาญี่ปุ่น และลิงก์ yui-yuto.com เสมอ\n"
        "5. ในบรรทัดแรกสุด ต้องพิมพ์ \"คีย์เวิร์ด: [คำศัพท์ 1 คำที่เลือก]\" เสมอ\n\n"
        "【ตัวอย่างรูปแบบข้อความ (บังคับใช้รูปแบบสั้นนี้อย่างเคร่งครัด)】\n"
        "คีย์เวิร์ด: ねこ\n"
        "🇯🇵 ねこ (เนโกะ) = แมว\n"
        "💡 ตัวอย่าง: ねこが好きです (ชอบแมวค่ะ)\n\n"
        "#เรียนภาษาญี่ปุ่น #ภาษาญี่ปุ่น yui-yuto.com"
    )
    
    tips_content = None
    keyword = None
    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1}/{max_retries} to generate and parse tips content...")
        try:
            raw_content = generator.generate_text(prompt, system_instruction)
            if not raw_content:
                print(f"LLM returned empty content on attempt {attempt + 1}.")
                continue
            
            # キーワードの抽出และ投稿用コンテンツの分離
            parsed_keyword = None
            tips_content_lines = []
            
            for line in raw_content.strip().split("\n"):
                match = re.match(r"^คีย์เวิร์ด\s*:\s*(.+)$", line, re.IGNORECASE)
                if match:
                    parsed_keyword = match.group(1).strip()
                else:
                    if not tips_content_lines and not line.strip():
                        continue
                    tips_content_lines.append(line)
            
            parsed_content = "\n".join(tips_content_lines).strip()
            
            if parsed_keyword and parsed_content:
                keyword = parsed_keyword
                tips_content = parsed_content
                print(f"Successfully generated and parsed content on attempt {attempt + 1}!")
                break
            else:
                print(f"Attempt {attempt + 1} failed: Keyword ('{parsed_keyword}') or content is missing.")
        except Exception as e:
            print(f"Error during attempt {attempt + 1}: {e}")
            
    if not tips_content or not keyword:
        print("CRITICAL ERROR: Failed to generate valid Japanese tips content and keyword after all retries.")
        sys.exit(1)
        
    print(f"Extracted Keyword: {keyword}")
    
    # 履歴への追加と保存
    if keyword not in history:
        history.append(keyword)
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            print(f"Successfully updated history.json with: '{keyword}'")
        except Exception as e:
            print(f"Failed to write history file: {e}")
        
    print("Generated Content (Cleaned):")
    print("-" * 40)
    print(tips_content)
    print("-" * 40)
    
    # 送信用のペイロード作成
    webhook_url = "https://hook.eu2.make.com/vqn11a5gws3fuatfkd3ykerdfgh23z7r"
    payload = {
        "message": tips_content
    }
    
    print(f"Sending request to Webhook: {webhook_url} ...")
    try:
        resp = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        print(f"Response Status Code: {resp.status_code}")
        print(f"Response Body: {resp.text}")
        if resp.status_code >= 200 and resp.status_code < 300:
            print("Successfully posted to Webhook!")
        else:
            print("Webhook returned error status code.")
            sys.exit(1)
    except Exception as e:
        print(f"Failed to post to Webhook: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
