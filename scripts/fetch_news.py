#!/usr/bin/env python3
"""
ดึงข่าวอวกาศล่าสุด -> ให้ AI สรุปเป็นภาษาไทย -> บันทึกเป็น docs/news.json
ไม่ต้องติดตั้งไลบรารีเพิ่ม (ใช้แค่ไลบรารีมาตรฐานของ Python)

ตัวแปร environment:
  GEMINI_API_KEY   (จำเป็น)  key จาก Google AI Studio
  AI_PROVIDER      gemini (ค่าเริ่มต้น) หรือ claude
  GEMINI_MODEL     (ไม่บังคับ) ถ้าไม่ตั้ง จะเลือกรุ่น flash ล่าสุดให้อัตโนมัติ
  ANTHROPIC_API_KEY / CLAUDE_MODEL  ใช้เมื่อ AI_PROVIDER=claude
  MAX_STORIES      จำนวนข่าวที่แสดง (ค่าเริ่มต้น 8)
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "docs" / "news.json"

NEWS_API = "https://api.spaceflightnewsapi.net/v4/articles/"
LAUNCH_API = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/"

MAX_STORIES = int(os.getenv("MAX_STORIES", "8"))
HOURS_BACK = int(os.getenv("HOURS_BACK", "36"))
UA = {"User-Agent": "space-news-th/1.0"}

CATEGORIES = ["จรวดและการปล่อย", "ดาราศาสตร์", "ดาวเทียม", "สำรวจอวกาศ", "สถานีอวกาศ", "ธุรกิจอวกาศ", "อื่นๆ"]


# ---------- HTTP ----------
def http_json(url, data=None, headers=None, timeout=60):
    hdrs = dict(UA)
    hdrs.update(headers or {})
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# ---------- 1. ดึงข่าว ----------
def fetch_articles():
    since = (datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = urllib.parse.urlencode({"limit": 40, "ordering": "-published_at", "published_at_gte": since})
    data = http_json(f"{NEWS_API}?{q}")
    articles = []
    for a in data.get("results", []):
        articles.append({
            "id": a.get("id"),
            "title": a.get("title", "").strip(),
            "summary": (a.get("summary") or "").strip()[:600],
            "source": a.get("news_site", ""),
            "url": a.get("url", ""),
            "image": a.get("image_url", ""),
            "published_at": a.get("published_at", ""),
        })
    return articles


def fetch_next_launch():
    try:
        data = http_json(f"{LAUNCH_API}?limit=1", timeout=30)
        l = (data.get("results") or [None])[0]
        if not l:
            return None
        return {
            "name": l.get("name", ""),
            "net": l.get("net", ""),
            "provider": (l.get("launch_service_provider") or {}).get("name", ""),
            "location": ((l.get("pad") or {}).get("location") or {}).get("name", ""),
            "status": (l.get("status") or {}).get("abbrev", ""),
        }
    except Exception as e:  # ไม่มีข้อมูลการปล่อยก็ยังแสดงข่าวได้
        print(f"[warn] ดึงข้อมูลการปล่อยจรวดไม่ได้: {e}", file=sys.stderr)
        return None


# ---------- 2. ให้ AI สรุป ----------
def build_prompt(articles):
    lines = [f'[{a["id"]}] ({a["source"]}) {a["title"]}\n{a["summary"]}' for a in articles]
    return f"""คุณเป็นบรรณาธิการข่าวอวกาศภาษาไทย ด้านล่างคือข่าวอวกาศภาษาอังกฤษจากหลายสำนักข่าว

งานของคุณ:
1. เลือกข่าวที่สำคัญและน่าสนใจที่สุด ไม่เกิน {MAX_STORIES} ข่าว
2. ถ้าหลายข่าวเป็นเรื่องเดียวกัน ให้รวมเป็นข่าวเดียว และใส่ id ของทุกข่าวที่เกี่ยวข้อง
3. เขียนหัวข้อภาษาไทยสั้น กระชับ (ไม่เกิน 70 ตัวอักษร)
4. สรุปเป็นภาษาไทยที่อ่านง่าย 2-3 ประโยค ใช้ข้อมูลจากข่าวเท่านั้น ห้ามแต่งเพิ่ม
5. ชื่อเฉพาะ (ชื่อจรวด ภารกิจ บริษัท) ให้คงเป็นภาษาอังกฤษ
6. เลือกหมวดจาก: {", ".join(CATEGORIES)}

ตอบเป็น JSON array เท่านั้น รูปแบบ:
[{{"ids": [123, 456], "title_th": "...", "summary_th": "...", "category": "..."}}]

ข่าว:
{chr(10).join(lines)}"""


GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


def gemini_candidates(key):
    """รายชื่อรุ่นที่จะลอง: รุ่นที่ตั้งเอง -> alias ล่าสุด -> รุ่น flash ที่ key นี้ใช้ได้จริง"""
    names = [m for m in [os.getenv("GEMINI_MODEL", "").strip(), "gemini-flash-latest", "gemini-flash-lite-latest"] if m]
    try:
        listing = http_json(f"{GEMINI_BASE}/models?pageSize=200", headers={"x-goog-api-key": key}, timeout=30)
        avail = [
            m["name"].split("/", 1)[-1] for m in listing.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
            and "flash" in m["name"]
            and not any(x in m["name"] for x in ("image", "tts", "audio", "live", "embedding"))
        ]
        # รุ่นเสถียรก่อนรุ่น preview, เลขเวอร์ชันใหม่ก่อน
        avail.sort(key=lambda n: ("preview" in n or "exp" in n, [-int(p) for p in __import__("re").findall(r"\d+", n)[:2]]))
        names += avail
    except Exception as e:
        print(f"[warn] ดูรายชื่อรุ่น Gemini ไม่ได้: {e}", file=sys.stderr)
    return list(dict.fromkeys(names))  # ตัดซ้ำ คงลำดับ


def ask_gemini(prompt):
    key = os.environ["GEMINI_API_KEY"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3},
    }
    last_err = None
    for model in gemini_candidates(key):
        try:
            data = http_json(f"{GEMINI_BASE}/models/{model}:generateContent", payload,
                             {"x-goog-api-key": key}, timeout=120)
            return data["candidates"][0]["content"]["parts"][0]["text"], model
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")[:300]
            print(f"[warn] {model}: HTTP {e.code} {detail}", file=sys.stderr)
            last_err = e
            if e.code in (401, 403):  # key ผิด ลองรุ่นอื่นก็ไม่ช่วย
                break
    raise SystemExit(f"เรียก Gemini ไม่สำเร็จ ({last_err}) — ตรวจ GEMINI_API_KEY ใน Secrets")


def ask_claude(prompt):
    key = os.environ["ANTHROPIC_API_KEY"]
    model = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
    payload = {"model": model, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]}
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    data = http_json("https://api.anthropic.com/v1/messages", payload, headers, timeout=120)
    return data["content"][0]["text"], model


def parse_json_array(text):
    text = text.strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("AI ไม่ได้ตอบเป็น JSON array")
    return json.loads(text[start:end + 1])


def summarize(articles):
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    prompt = build_prompt(articles)
    text, model = ask_claude(prompt) if provider == "claude" else ask_gemini(prompt)
    picks = parse_json_array(text)

    by_id = {a["id"]: a for a in articles}
    stories = []
    for p in picks[:MAX_STORIES]:
        srcs = [by_id[i] for i in p.get("ids", []) if i in by_id]
        if not srcs:
            continue
        cat = p.get("category", "อื่นๆ")
        stories.append({
            "title_th": p.get("title_th", "").strip(),
            "summary_th": p.get("summary_th", "").strip(),
            "category": cat if cat in CATEGORIES else "อื่นๆ",
            "title_en": srcs[0]["title"],
            "image": next((s["image"] for s in srcs if s["image"]), ""),
            "published_at": srcs[0]["published_at"],
            "sources": [{"name": s["source"], "url": s["url"]} for s in srcs],
        })
    return stories, f"{provider}:{model}"


# ---------- 3. บันทึก ----------
def main():
    articles = fetch_articles()
    print(f"ดึงข่าวได้ {len(articles)} ข่าว")
    if not articles:
        print("ไม่มีข่าวใหม่ ใช้ไฟล์เดิม")
        return

    stories, model = summarize(articles)
    print(f"สรุปได้ {len(stories)} ข่าว ด้วย {model}")
    if not stories:
        sys.exit("AI ไม่ได้คืนข่าวที่ใช้ได้ — ไม่เขียนทับไฟล์เดิม")

    out = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model,
        "next_launch": fetch_next_launch(),
        "stories": stories,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกแล้ว: {OUT_FILE}")


if __name__ == "__main__":
    main()
