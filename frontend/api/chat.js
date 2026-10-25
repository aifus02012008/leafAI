/**
 * LEAF_AI — Vercel Serverless Function: POST /api/chat
 * Kỹ sư AI Vườn Vải Lục Ngạn — gọi Google Gemini qua REST (không cần SDK).
 *
 * Biến môi trường (Vercel → Project → Settings → Environment Variables):
 *   GEMINI_API_KEY  (bắt buộc)
 *   GEMINI_MODEL    (tuỳ chọn, mặc định gemini-2.5-flash)
 *
 * Request : { message: string, history?: [{ role: 'user' | 'model', text: string }] }
 * Response: { success: true, reply: string, model: string }
 */

const DEFAULT_MODEL = 'gemini-2.5-flash';
const MAX_MESSAGE = 2000;
const MAX_HISTORY = 10;
const UPSTREAM_TIMEOUT_MS = 25000;

const SYSTEM_PROMPT = `Bạn là "Kỹ sư AI Vườn Vải" của ứng dụng LEAF_AI — kỹ sư bảo vệ thực vật chuyên cây vải thiều (Litchi chinensis) vùng Lục Ngạn, Bắc Giang.
Nhiệm vụ: tư vấn cho nông dân về bệnh hại trên lá, lộc, hoa vải và quy trình IPM/VietGAP.
5 bệnh/dịch hại trọng tâm mà mô hình LEAF_AI nhận diện: Thán thư (Colletotrichum gloeosporioides), Sương mai (Peronophythora litchii), Cháy lá (Pestalotiopsis spp.), Đốm rong (Cephaleuros virescens), Nhện lông nhung (Aceria litchii).
Quy tắc trả lời:
- Xưng "em", gọi người hỏi là "bà con". Tiếng Việt dễ hiểu, ngắn gọn (tối đa khoảng 180 từ), dùng gạch đầu dòng khi liệt kê.
- Khi chẩn đoán từ mô tả: nêu bệnh khả năng cao nhất, dấu hiệu phân biệt, rồi biện pháp theo thứ tự canh tác → sinh học → hoá học (chỉ khi vượt ngưỡng).
- Hoá học: chỉ nêu hoạt chất (không quảng cáo thương hiệu), nhắc nguyên tắc 4 đúng và thời gian cách ly (PHI) theo nhãn; không phun khi hoa nở rộ.
- Nếu mô tả chưa đủ, hỏi lại 1–2 ý (màu vết bệnh, vị trí trên lá, lộc non hay lá già, thời tiết) và gợi ý chụp ảnh lá ở mục "Quét lá".
- Câu hỏi ngoài lĩnh vực cây trồng: lịch sự từ chối và hướng về chủ đề vườn vải.
- Không bịa số liệu liều lượng; khuyên bà con đọc nhãn thuốc và hỏi cán bộ BVTV địa phương khi cần.`;

// Giới hạn tần suất đơn giản theo IP (best-effort, theo từng instance)
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 12;
const hits = new Map();

function rateLimited(ip) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter((t) => now - t < RATE_WINDOW_MS);
  list.push(now);
  hits.set(ip, list);
  if (hits.size > 500) hits.clear();
  return list.length > RATE_MAX;
}

function readBody(req) {
  if (req.body && typeof req.body === 'object') return Promise.resolve(req.body);
  if (typeof req.body === 'string') {
    try { return Promise.resolve(JSON.parse(req.body)); } catch { return Promise.resolve({}); }
  }
  return new Promise((resolve) => {
    let raw = '';
    req.on('data', (c) => { raw += c; if (raw.length > 64_000) req.destroy(); });
    req.on('end', () => { try { resolve(JSON.parse(raw || '{}')); } catch { resolve({}); } });
    req.on('error', () => resolve({}));
  });
}

function sanitizeHistory(history) {
  if (!Array.isArray(history)) return [];
  return history
    .filter((h) => h && (h.role === 'user' || h.role === 'model') && typeof h.text === 'string' && h.text.trim())
    .slice(-MAX_HISTORY)
    .map((h) => ({ role: h.role, parts: [{ text: h.text.slice(0, MAX_MESSAGE) }] }));
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ success: false, error: 'Method not allowed' });

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    // 503 → client tự chuyển sang trả lời ngoại tuyến
    return res.status(503).json({ success: false, error: 'GEMINI_API_KEY chưa được cấu hình' });
  }

  const ip = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown').split(',')[0].trim();
  if (rateLimited(ip)) {
    return res.status(429).json({ success: false, error: 'Too many requests' });
  }

  const body = await readBody(req);
  const message = String(body.message || '').trim().slice(0, MAX_MESSAGE);
  if (!message) return res.status(400).json({ success: false, error: 'Tin nhắn không được để trống' });

  const model = process.env.GEMINI_MODEL || DEFAULT_MODEL;
  const contents = [...sanitizeHistory(body.history), { role: 'user', parts: [{ text: message }] }];
  // Gemini yêu cầu lượt đầu tiên là 'user'
  while (contents.length && contents[0].role !== 'user') contents.shift();

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), UPSTREAM_TIMEOUT_MS);

  try {
    const upstream = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-goog-api-key': apiKey },
        signal: ctrl.signal,
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
          contents,
          generationConfig: {
            temperature: 0.4,
            maxOutputTokens: 1024,
            // Tắt "thinking" của 2.5-flash để phản hồi nhanh hơn trên mobile
            ...(model.includes('2.5-flash') ? { thinkingConfig: { thinkingBudget: 0 } } : {})
          }
        })
      }
    );

    const data = await upstream.json().catch(() => ({}));
    if (!upstream.ok) {
      console.error('[chat] Gemini error', upstream.status, JSON.stringify(data).slice(0, 500));
      const status = upstream.status === 429 ? 429 : 502;
      return res.status(status).json({ success: false, error: 'Gemini upstream error' });
    }

    const reply = (data.candidates?.[0]?.content?.parts || [])
      .map((p) => p.text || '')
      .join('')
      .trim();

    if (!reply) {
      return res.status(502).json({ success: false, error: 'Empty reply', finishReason: data.candidates?.[0]?.finishReason });
    }

    return res.status(200).json({ success: true, reply, model });
  } catch (err) {
    const timeout = err?.name === 'AbortError';
    console.error('[chat] request failed', timeout ? 'timeout' : err);
    return res.status(timeout ? 504 : 500).json({ success: false, error: timeout ? 'Upstream timeout' : 'Internal error' });
  } finally {
    clearTimeout(timer);
  }
};
