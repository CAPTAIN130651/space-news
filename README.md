# 🛰️ ข่าวอวกาศรายวัน (ภาษาไทย)

ดึงข่าวอวกาศจากทั่วโลกทุกเช้า → Gemini สรุปเป็นภาษาไทยพร้อมแหล่งที่มา → แสดงเป็น widget ลอยบน desktop Mac และเปิดเป็นเว็บได้

```
Spaceflight News API ─┐
Launch Library 2 ─────┼─► GitHub Actions (05:47 ทุกวัน) ─► Gemini สรุปไทย ─► docs/news.json
                      │                                                         │
                      │                                    GitHub Pages ◄───────┘
                      │                                         │
                      └───────────────── Übersicht widget ◄─────┘  (+ หน้าเว็บ docs/index.html)
```

ทั้งหมดฟรี ไม่ต้องเปิดเครื่องค้างไว้

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `scripts/fetch_news.py` | ดึงข่าว + ให้ AI สรุป + บันทึก JSON |
| `.github/workflows/daily.yml` | ตั้งเวลารันทุกเช้าบน GitHub |
| `docs/news.json` | ข้อมูลข่าว (ถูกเขียนทับทุกวัน) |
| `docs/index.html` | หน้าเว็บดูข่าว (เปิดจากมือถือได้) |
| `space-news.widget/index.jsx` | widget สำหรับ Übersicht |

## ติดตั้ง (ประมาณ 15 นาที)

### 1. เอา Gemini API key (ฟรี)
1. เข้า https://aistudio.google.com/apikey แล้วล็อกอิน Google
2. กด **Create API key** แล้วคัดลอกเก็บไว้

### 2. สร้าง repo บน GitHub
1. สร้าง repo ใหม่ชื่อ `space-news` ตั้งเป็น **Public** (GitHub Pages ฟรีต้องเป็น public)
2. อัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้ (รวมโฟลเดอร์ `.github` ด้วย — บน Mac กด `Cmd+Shift+.` เพื่อให้เห็นไฟล์ที่ซ่อน)

### 3. ใส่ key และเปิดสิทธิ์
1. **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `GEMINI_API_KEY` / Secret: key จากข้อ 1
2. **Settings → Actions → General → Workflow permissions** เลือก **Read and write permissions** → Save
3. **Settings → Pages** → Source: **Deploy from a branch** → Branch: `main` / โฟลเดอร์ `/docs` → Save

### 4. รันครั้งแรก
แท็บ **Actions → Daily space news (TH) → Run workflow**
รอ 1-2 นาที แล้วเปิด `https://ชื่อผู้ใช้.github.io/space-news/` ต้องเห็นข่าว

### 5. ติดตั้ง widget บน Mac
1. ติดตั้ง Übersicht: ดาวน์โหลดจาก https://tracesof.net/uebersicht/ หรือใช้ `brew install --cask ubersicht`
2. เปิดไฟล์ `space-news.widget/index.jsx` แก้บรรทัด
   ```js
   const NEWS_URL = "https://YOUR-USERNAME.github.io/space-news/news.json";
   ```
   เป็นชื่อผู้ใช้ GitHub ของคุณ
3. คลิกไอคอน Übersicht บนแถบเมนู → **Open Widgets Folder** แล้วลากโฟลเดอร์ `space-news.widget` ไปใส่
4. widget จะขึ้นที่มุมขวาบนของ desktop ทันที
5. ตั้งให้ Übersicht เปิดตอนเปิดเครื่อง: เมนู Übersicht → **Preferences → Launch Übersicht when I login**

## ปรับแต่ง

**widget** (`index.jsx` ด้านบนสุด)
- `POSITION` — ตำแหน่ง เช่น `{ top: "40px", left: "24px" }` ย้ายไปซ้าย
- `WIDTH` — ความกว้าง
- `MAX_SHOWN` — จำนวนข่าวที่แสดง
- คลิกหัวข้อข่าวหรือชื่อแหล่งข่าว = เปิดข่าวต้นฉบับในเบราว์เซอร์

**เวลารัน** (`daily.yml`) — cron ใช้เวลา UTC (= เวลาไทย − 7 ชม.) เช่น `"0 0 * * *"` = 07:00 น.

**จำนวนข่าว / ช่วงเวลา** — เพิ่ม Variable `MAX_STORIES` (ค่าเริ่มต้น 8) ใน Settings → Secrets and variables → Actions → Variables (ใช้ที่เดียวกันตั้ง `GEMINI_MODEL` ได้)

## เปลี่ยนไปใช้ Claude ภายหลัง
1. เพิ่ม secret `ANTHROPIC_API_KEY`
2. **Settings → Secrets and variables → Actions → แท็บ Variables** เพิ่ม `AI_PROVIDER` = `claude`

ไม่ต้องแก้โค้ด

## ทดสอบบนเครื่อง
```bash
export GEMINI_API_KEY="key ของคุณ"
python3 scripts/fetch_news.py
```

## แก้ปัญหา
| อาการ | วิธีแก้ |
|---|---|
| widget ขึ้น "โหลดข่าวไม่ได้" | เช็ก `NEWS_URL` ว่าเปิดในเบราว์เซอร์ได้ |
| Actions ล้มที่ขั้น push | ยังไม่ได้เปิด Read and write permissions (ข้อ 3.2) |
| Actions ล้มที่ขั้น Fetch, error 429 | ใช้ free tier เกินโควตา รอวันถัดไป หรือเปลี่ยน `GEMINI_MODEL` เป็น `gemini-2.5-flash-lite` |
| Actions ล้ม error 404 ที่ Gemini | ชื่อรุ่นอาจถูกเลิกใช้ ตั้ง `GEMINI_MODEL` เป็นรุ่นล่าสุดจาก AI Studio |

## แหล่งข้อมูล
- ข่าว: [Spaceflight News API](https://spaceflightnewsapi.net) (รวมข่าวจาก NASA, ESA, SpaceNews, Space.com ฯลฯ)
- การปล่อยจรวด: [Launch Library 2](https://thespacedevs.com/llapi) (free tier จำกัดจำนวนครั้งต่อชั่วโมง ใช้วันละครั้งไม่มีปัญหา)
