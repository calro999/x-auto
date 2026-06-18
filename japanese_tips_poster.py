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
        "ให้สร้างโพสต์แนะนำเทคนิคการจำ คำศัพท์ หรือประโยคภาษาญี่ปุ่นสั้นๆ 1 ข้อความสำหรับลงโซเชียลมีเดีย (X/Twitter) "
        "โดยอธิบายทุกอย่างเป็นภาษาไทยอย่างละเอียดและเข้าใจง่าย ห้ามใช้คำเกริ่นนำหรือคำพูดทักทายอื่นใดนอกจากตัวโพสต์ที่จะใช้งานจริงเท่านั้น\n"
        "【กฎสำคัญที่สุด】ห้ามเลือกคำศัพท์ ไวยากรณ์ หรือหัวข้อที่ซ้ำกับคำในรายการที่เคยใช้ไปแล้วด้านล่างนี้เด็ดขาด! ต้องเลือกเรื่องใหม่ทุกครั้ง"
    )
    
    history_str = ", ".join(history) if history else "ไม่มี (นี่เป็นครั้งแรก)"
    
    prompt = (
        "สร้างเนื้อหาแนะนำภาษาญี่ปุ่นสำหรับคนไทยเริ่มต้นเรียนภาษาญี่ปุ่น (ระดับ N5) 1 โพสต์ เพื่อโพสต์ลง X (Twitter)\n\n"
        "【รายการคำศัพท์/หัวข้อที่เคยใช้ไปแล้ว (ห้ามซ้ำเด็ดขาด!)】\n"
        f"{history_str}\n\n"
        "【เงื่อนไขสำคัญ】\n"
        "1. อธิบายเป็นภาษาไทยเป็นหลัก เพื่อให้คนที่พูดญี่ปุ่นไม่ได้เลยเข้าใจได้ง่าย\n"
        "2. เลือกหัวข้อระดับเริ่มต้นมากๆ ที่ไม่ซ้ำกับรายการด้านบน (เช่น การทักทาย, คำศัพท์ในชีวิตประจำวัน, คำช่วยพื้นฐาน, หรือประโยคง่ายๆ)\n"
        "3. มีตัวอย่างคำศัพท์ภาษาญี่ปุ่น, คำอ่านภาษาไทย และคำแปลภาษาไทย\n"
        "4. ห้ามใช้ตัวหนาแบบ Markdown (ห้ามใส่ **) ให้ใช้ข้อความธรรมดาเท่านั้น\n"
        "5. ลงท้ายด้วยแฮชแท็ก #เรียนภาษาญี่ปุ่น #ภาษาญี่ปุ่น #N5 และต่อท้ายด้วยลิงก์เว็บไซต์ yui-yuto.com เสมอ\n"
        "6. ในบรรทัดแรกสุดของข้อความที่ส่งกลับมา ให้พิมพ์คำว่า \"คีย์เวิร์ด: [คำศัพท์หรือคำภาษาญี่ปุ่นสั้นๆ 1 คำที่เลือก]\" เสมอ (ห้ามใช้การผสมคำช่วยที่ไม่มีความหมาย เช่น 'はとก' หรือประโยคยาว ให้เลือกคำเดี่ยวๆ หรือหัวข้อสั้นๆ เช่น 'ねこ', '美味しい', 'ありがとう', 'คำช่วย は') เพื่อใช้ตรวจสอบประวัติ\n\n"
        "【ตัวอย่างรูปแบบข้อความ】\n"
        "คีย์เวิร์ด: ...\n"
        "เรียนภาษาญี่ปุ่นง่ายๆ วันนี้เสนอคำว่า \"...\"\n"
        "คำนี้หมายถึง \"...\" ใช้เวลาที่ต้องการ...\n"
        "ตัวอย่าง:\n"
        "... (อ่านว่า: ...) = ...\n\n"
        "#เรียนภาษาญี่ปุ่น #ภาษาญี่ปุ่น #N5 yui-yuto.com"
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
