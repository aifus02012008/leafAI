/**
 * LEAF_AI — Trợ lý kỹ sư AI (assistant.html)
 * Gửi câu hỏi tới /api/chat/, có trả lời ngoại tuyến khi backend không chạy.
 * Hỗ trợ ?q=... để gửi sẵn câu hỏi từ trang chẩn đoán / trang bệnh.
 */
(function () {
  'use strict';
  const { escapeHtml, params } = window.Leaf;
  const $ = (id) => document.getElementById(id);
  const api = new LeafApiService();

  const thread = $('thread');
  const input = $('chatInput');
  const sendBtn = $('btnSend');
  let sending = false;

  const WELCOME = '<p>Xin chào! Mình là trợ lý chuyên về bệnh hại trên cây vải thiều.</p><p>Bạn có thể mô tả vết bệnh (màu sắc, vị trí ở chóp, mép hay mặt dưới lá, lộc non hay lá già) hoặc hỏi về cách xử lý theo hướng IPM.</p>';

  /** Markdown tối giản cho câu trả lời dạng text: in đậm, xuống dòng, gạch đầu dòng */
  function mdToHtml(text) {
    const lines = escapeHtml(text).split(/\n/);
    let html = '';
    let inList = false;
    lines.forEach((line) => {
      const li = line.match(/^\s*(?:[-*•]|\d+\.)\s+(.*)/);
      if (li) {
        if (!inList) { html += '<ul>'; inList = true; }
        html += `<li>${li[1]}</li>`;
      } else {
        if (inList) { html += '</ul>'; inList = false; }
        if (line.trim()) html += `<p>${line}</p>`;
      }
    });
    if (inList) html += '</ul>';
    return html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  }

  function addMessage(html, who = 'bot') {
    const el = document.createElement('div');
    el.className = `msg${who === 'me' ? ' me' : ''}`;
    el.innerHTML = `<span class="avatar" aria-hidden="true"><i class="bi ${who === 'me' ? 'bi-person' : 'bi-flower1'}"></i></span><div class="bubble">${html}</div>`;
    thread.appendChild(el);
    thread.scrollTop = thread.scrollHeight;
    return el;
  }

  async function send(text) {
    const msg = (text ?? input.value).trim();
    if (!msg || sending) return;
    sending = true;
    sendBtn.disabled = true;
    input.value = '';
    autosize();

    addMessage(`<p>${escapeHtml(msg)}</p>`, 'me');
    const typing = addMessage('<span class="typing-dots" aria-label="Đang trả lời"><i></i><i></i><i></i></span>');

    try {
      const res = await api.sendChatMessage(msg);
      const html = res.offline ? res.reply_html : mdToHtml(res.reply || '');
      typing.querySelector('.bubble').innerHTML = html || '<p>Mình chưa có câu trả lời cho câu này. Bạn thử diễn đạt khác nhé.</p>';
    } catch {
      typing.querySelector('.bubble').innerHTML = '<p>Không gửi được câu hỏi. Kiểm tra kết nối mạng rồi thử lại.</p>';
    } finally {
      thread.scrollTop = thread.scrollHeight;
      sending = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  function autosize() {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
  }

  function reset() {
    thread.innerHTML = '';
    addMessage(WELCOME);
  }

  $('composer').addEventListener('submit', (e) => { e.preventDefault(); send(); });
  input.addEventListener('input', autosize);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); }
  });
  document.querySelectorAll('.suggest button').forEach((b) => b.addEventListener('click', () => send(b.textContent)));
  $('btnNewChat').addEventListener('click', () => { reset(); input.focus(); });

  reset();
  const q = params.get('q');
  if (q) send(q);
})();
