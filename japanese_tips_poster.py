import os
import sys
import requests
from article_generator import ArticleGenerator

def main():
    print("Starting Japanese Tips Generator...")
    generator = ArticleGenerator()
    
    system_instruction = (
        "คุณเป็นครูสอนภาษาญี่ปุ่นให้กับคนไทยที่ไม่มีพื้นฐานเลย (ระดับ N5) "
        "ให้สร้างโพสต์แนะนำเทคนิคการจำ คำศัพท์ หรือประโยคภาษาญี่ปุ่นสั้นๆ 1 ข้อความสำหรับลงโซเชียลมีเดีย (X/Twitter) "
        "โดยอธิบายทุกอย่างเป็นภาษาไทยอย่างละเอียดและเข้าใจง่าย ห้ามใช้คำเกริ่นนำหรือคำพูดทักทายอื่นใดนอกจากตัวโพสต์ที่จะใช้งานจริงเท่านั้น"
    )
    
    prompt = (
        "สร้างเนื้อหาแนะนำภาษาญี่ปุ่นสำหรับคนไทยเริ่มต้นเรียนภาษาญี่ปุ่น (ระดับ N5) 1 โพสต์ เพื่อโพสต์ลง X (Twitter)\n\n"
        "【เงื่อนไขสำคัญ】\n"
        "1. อธิบายเป็นภาษาไทยเป็นหลัก เพื่อให้คนที่พูดญี่ปุ่นไม่ได้เลยเข้าใจได้ง่าย\n"
        "2. เลือกหัวข้อระดับเริ่มต้นมากๆ (เช่น การทักทายง่ายๆ, คำศัพท์จำเป็นในชีวิตประจำวัน, หรือความแตกต่างของคำช่วยพื้นฐาน)\n"
        "3. มีตัวอย่างคำศัพท์ภาษาญี่ปุ่น, คำอ่านภาษาไทย และคำแปลภาษาไทย\n"
        "4. ห้ามใช้ตัวหนาแบบ Markdown (ห้ามใส่ **) ให้ใช้ข้อความธรรมดาเท่านั้น\n"
        "5. ลงท้ายด้วยแฮชแท็ก #เรียนภาษาญี่ปุ่น #ภาษาญี่ปุ่น #N5 และต่อท้ายด้วยลิงก์เว็บไซต์ yui-yuto.com เสมอ\n\n"
        "【ตัวอย่างรูปแบบข้อความ】\n"
        "เรียนภาษาญี่ปุ่นง่ายๆ วันนี้เสนอคำว่า \"...\"\n"
        "คำนี้หมายถึง \"...\" ใช้เวลาที่ต้องการ...\n"
        "ตัวอย่าง:\n"
        "... (อ่านว่า: ...) = ...\n\n"
        "#เรียนภาษาญี่ปุ่น #ภาษาญี่ปุ่น #N5 yui-yuto.com"
    )
    
    try:
        tips_content = generator.generate_text(prompt, system_instruction)
    except Exception as e:
        print(f"Error during LLM generation: {e}")
        tips_content = None
        
    if not tips_content:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print("Error: Generated content is empty in GitHub Actions.")
            sys.exit(1)
        else:
            print("WARNING: All free LLM APIs failed. Since this is a local dry-run, using dummy tips content.")
            tips_content = (
                "เรียนภาษาญี่ปุ่นง่ายๆ วันนี้เสนอคำช่วย 「は (wa)」 และ 「が (ga)」 ที่มือใหม่มักจะสับสนครับ!\n\n"
                "・は (wa) ใช้ชี้หัวข้อหลักของประโยคทั่วไป เช่น:\n"
                "私はタイ人です (Watashi wa tai-jin desu) = ฉันเป็นคนไทย\n\n"
                "・が (ga) ใช้เน้นเจาะจงประธานในประโยคเป็นพิเศษ เช่น:\n"
                "私がタイ人です (Watashi ga tai-jin desu) = (ในกลุ่มคนเหล่านี้) ฉันนี่แหละที่เป็นคนไทย\n\n"
                "#เรียนภาษาญี่ปุ่น #ภาษาญี่ปุ่น #N5 yui-yuto.com"
            )
        
    print("Generated Content:")
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
