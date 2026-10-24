// ข่าวอวกาศรายวัน (ภาษาไทย) — widget สำหรับ Übersicht
// แก้ NEWS_URL เป็นลิงก์ GitHub Pages ของคุณ
import { run, css } from "uebersicht";

const NEWS_URL = "https://YOUR-USERNAME.github.io/space-news/news.json";

// ตำแหน่งบนจอ: เปลี่ยน top/right/left ได้
const POSITION = { top: "40px", right: "24px" };
const WIDTH = 380;
const MAX_SHOWN = 6;

export const command = `curl -sfL --max-time 20 "${NEWS_URL}?t=$(date +%s)"`;
export const refreshFrequency = 5 * 60 * 1000; // ดึงใหม่ทุก 5 นาที

const CAT_COLOR = {
  "จรวดและการปล่อย": "#ff8a5c",
  "ดาราศาสตร์": "#b79cff",
  "ดาวเทียม": "#5cc8ff",
  "สำรวจอวกาศ": "#7be0a8",
  "สถานีอวกาศ": "#ffd166",
  "ธุรกิจอวกาศ": "#f2a7d8",
  "อื่นๆ": "#a0a8b8",
};

const open = (url) => run(`open "${url.replace(/"/g, "")}"`);

const thaiTime = (iso) =>
  new Date(iso).toLocaleString("th-TH", {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });

const ago = (iso) => {
  const h = Math.floor((Date.now() - new Date(iso)) / 3.6e6);
  if (h < 1) return "เมื่อสักครู่";
  if (h < 24) return `${h} ชม.ที่แล้ว`;
  return `${Math.floor(h / 24)} วันที่แล้ว`;
};

const countdown = (iso) => {
  let s = Math.floor((new Date(iso) - Date.now()) / 1000);
  if (s <= 0) return "กำลังปล่อย / ปล่อยแล้ว";
  const d = Math.floor(s / 86400); s %= 86400;
  const h = Math.floor(s / 3600); s %= 3600;
  const m = Math.floor(s / 60);
  return `T- ${d > 0 ? d + " วัน " : ""}${h} ชม. ${m} นาที`;
};

// ---------- สไตล์ ----------
export const className = css`
  top: ${POSITION.top};
  ${POSITION.right ? `right: ${POSITION.right};` : `left: ${POSITION.left};`}
  width: ${WIDTH}px;
  font-family: -apple-system, "SF Pro Text", "Thonburi", sans-serif;
  color: #e8ecf4;
`;

const panel = css`
  background: rgba(12, 16, 28, 0.62);
  backdrop-filter: blur(22px) saturate(140%);
  -webkit-backdrop-filter: blur(22px) saturate(140%);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 18px;
  padding: 16px 16px 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
`;
const header = css`
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 12px;
`;
const h1 = css`font-size: 15px; font-weight: 700; letter-spacing: 0.2px;`;
const meta = css`font-size: 10.5px; opacity: 0.55;`;
const launch = css`
  background: linear-gradient(135deg, rgba(255,138,92,0.18), rgba(183,156,255,0.14));
  border-radius: 12px; padding: 10px 12px; margin-bottom: 12px;
`;
const launchLabel = css`font-size: 10px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7;`;
const launchName = css`font-size: 13px; font-weight: 600; margin: 3px 0 2px;`;
const launchCd = css`font-size: 15px; font-weight: 700; color: #ffb38f; font-variant-numeric: tabular-nums;`;
const story = css`
  padding: 10px 0; border-top: 1px solid rgba(255, 255, 255, 0.07);
  cursor: default;
`;
const chip = (c) => css`
  display: inline-block; font-size: 10px; font-weight: 600;
  color: ${c}; background: ${c}22; border-radius: 6px; padding: 1px 7px;
  margin-right: 6px;
`;
const title = css`
  font-size: 13.5px; font-weight: 650; line-height: 1.4; margin: 5px 0 3px;
  cursor: pointer;
  &:hover { color: #9fd3ff; }
`;
const summary = css`
  font-size: 12px; line-height: 1.55; opacity: 0.82;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
`;
const sources = css`margin-top: 5px; font-size: 10.5px; opacity: 0.6;`;
const srcLink = css`
  cursor: pointer; text-decoration: underline; text-underline-offset: 2px;
  margin-right: 8px;
  &:hover { opacity: 1; color: #9fd3ff; }
`;

// ---------- แสดงผล ----------
export const render = ({ output, error }) => {
  let data;
  try { data = JSON.parse(output); } catch (e) { data = null; }

  if (error || !data) {
    return (
      <div className={panel}>
        <div className={h1}>🛰️ ข่าวอวกาศวันนี้</div>
        <div className={meta} style={{ marginTop: 8 }}>
          โหลดข่าวไม่ได้ — ตรวจ NEWS_URL หรืออินเทอร์เน็ต
        </div>
      </div>
    );
  }

  const nl = data.next_launch;
  return (
    <div className={panel}>
      <div className={header}>
        <div className={h1}>🛰️ ข่าวอวกาศวันนี้</div>
        <div className={meta}>อัปเดต {thaiTime(data.updated_at)}</div>
      </div>

      {nl && nl.net && (
        <div className={launch}>
          <div className={launchLabel}>ปล่อยจรวดครั้งถัดไป</div>
          <div className={launchName}>{nl.name}</div>
          <div className={launchCd}>{countdown(nl.net)}</div>
          <div className={meta}>{thaiTime(nl.net)} · {nl.location}</div>
        </div>
      )}

      {data.stories.length === 0 && (
        <div className={meta} style={{ padding: "8px 0" }}>ยังไม่มีข่าว — รอการอัปเดตรอบแรก</div>
      )}

      {data.stories.slice(0, MAX_SHOWN).map((s, i) => (
        <div className={story} key={i}>
          <span className={chip(CAT_COLOR[s.category] || CAT_COLOR["อื่นๆ"])}>{s.category}</span>
          <span className={meta}>{ago(s.published_at)}</span>
          <div className={title} onClick={() => open(s.sources[0].url)}>{s.title_th}</div>
          <div className={summary}>{s.summary_th}</div>
          <div className={sources}>
            ที่มา:{" "}
            {s.sources.map((src, j) => (
              <span key={j} className={srcLink} onClick={() => open(src.url)}>{src.name}</span>
            ))}
          </div>
        </div>
      ))}

      <div className={meta} style={{ textAlign: "right", paddingTop: 6 }}>
        สรุปโดย AI · ตรวจสอบรายละเอียดจากแหล่งข่าวต้นฉบับ
      </div>
    </div>
  );
};
