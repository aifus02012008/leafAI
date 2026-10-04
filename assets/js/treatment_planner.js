/**
 * LEAF_AI — Bộ lập phác đồ điều trị (bản chạy trên trình duyệt).
 * Cùng thuật toán với ml/hf-space/treatment.py để ứng dụng vẫn lập được lịch khi
 * máy chủ đang khởi động hoặc mất sóng ngoài vườn. Kết quả gắn generated_by = 'offline'.
 */
(function () {
  'use strict';

  const KB_URL = 'assets/data/treatment_protocols.json';

  const SCHEDULES = {
    nhe: [[0, 'cultural'], [1, 'biological'], [3, 'monitor'], [7, 'biological'], [10, 'evaluate'], [10, 'chemical_conditional']],
    trung_binh: [[0, 'cultural'], [1, 'biological'], [3, 'monitor'], [5, 'chemical'], [12, 'monitor'], [14, 'chemical_conditional'], [21, 'evaluate']],
    nang: [[0, 'cultural'], [1, 'chemical'], [4, 'monitor'], [8, 'chemical'], [11, 'biological'], [15, 'monitor'], [21, 'evaluate']]
  };

  const SEVERITY_ALIASES = {
    nhe: 'nhe', 'nhẹ': 'nhe', low: 'nhe', mild: 'nhe',
    trung_binh: 'trung_binh', 'trung bình': 'trung_binh', medium: 'trung_binh', moderate: 'trung_binh',
    nang: 'nang', 'nặng': 'nang', 'nghiêm trọng': 'nang', high: 'nang', severe: 'nang'
  };

  const DISEASE_ALIASES = {
    than_thu: 'anthracnose', colletotrichum: 'anthracnose',
    suong_mai: 'downy_blight', downy: 'downy_blight', peronophythora: 'downy_blight',
    chay_la: 'leaf_blight', pestalotiopsis: 'leaf_blight',
    dom_rong: 'algal_spot', algal: 'algal_spot', cephaleuros: 'algal_spot',
    nhen_long_nhung: 'erinose', erinose_mite: 'erinose', leaf_mite: 'erinose', leaf_mites: 'erinose', mite: 'erinose', aceria: 'erinose'
  };

  const GENERAL_RULES = [
    'Đúng thuốc: chỉ dùng thuốc có trong danh mục được phép, đúng đối tượng gây hại.',
    'Đúng liều: pha theo liều ghi trên nhãn, không tự tăng nồng độ.',
    'Đúng lúc: phun sáng sớm hoặc chiều mát, khi trời không mưa; không phun khi hoa nở rộ.',
    'Đúng cách: phun ướt đều hai mặt lá, chú ý lộc non; mang đồ bảo hộ khi pha và phun.',
    'Luân phiên nhóm hoạt chất (mã FRAC/IRAC khác nhau) giữa các lần phun để hạn chế kháng thuốc.',
    'Ghi nhật ký mỗi lần phun (ngày, hoạt chất, liều) để tính thời gian cách ly trước thu hoạch.'
  ];

  let kbPromise = null;
  const loadKB = () => {
    if (!kbPromise) {
      kbPromise = fetch(KB_URL).then((r) => {
        if (!r.ok) throw new Error('Không tải được kho phác đồ');
        return r.json();
      }).catch((err) => { kbPromise = null; throw err; });
    }
    return kbPromise;
  };

  const norm = (s) => String(s || '').normalize('NFC').trim().toLowerCase();

  function resolveDisease(kb, name) {
    const key = norm(name).replace(/[\s-]+/g, '_');
    if (kb.diseases[key]) return key;
    const byClass = Object.keys(kb.diseases).find((k) => kb.diseases[k].class.toLowerCase() === key);
    return byClass || DISEASE_ALIASES[key] || null;
  }

  const resolveSeverity = (v) => SEVERITY_ALIASES[norm(v || 'trung_binh')] || 'trung_binh';

  /** Ngày dạng YYYY-MM-DD, cộng ngày theo UTC để không lệch múi giờ */
  function addDays(iso, n) {
    const [y, m, d] = iso.split('-').map(Number);
    const t = new Date(Date.UTC(y, m - 1, d + n));
    return t.toISOString().slice(0, 10);
  }

  function todayIso() {
    const t = new Date();
    return new Date(Date.UTC(t.getFullYear(), t.getMonth(), t.getDate())).toISOString().slice(0, 10);
  }

  function pickChemicals(options, count) {
    const picks = [];
    for (let i = 0; i < count && options.length; i += 1) {
      if (!picks.length) { picks.push(options[0]); continue; }
      const prev = picks[picks.length - 1].group;
      const next = options.find((o) => o.group !== prev && !picks.includes(o));
      picks.push(next || options[i % options.length]);
    }
    return picks;
  }

  function build(kb, { disease, severity = 'trung_binh', growth_stage = 'loc_non', area_m2 = 1000, start_date = null, days_to_harvest = null } = {}) {
    const key = resolveDisease(kb, disease);
    if (!key) throw new Error(`Chưa có phác đồ cho lớp "${disease}".`);
    const d = kb.diseases[key];
    const sev = resolveSeverity(severity);
    const stage = kb.growth_stages[growth_stage] ? growth_stage : 'loc_non';
    const start = start_date || todayIso();
    const area = Math.max(1, Number(area_m2) || 1000);
    const guard = Number(kb.phi_guard_days);
    const harvest = days_to_harvest === null || days_to_harvest === '' || days_to_harvest === undefined ? null : Number(days_to_harvest);

    const schedule = SCHEDULES[sev];
    const nChem = schedule.filter(([, t]) => t.startsWith('chemical')).length;
    const chems = pickChemicals(d.chemical, nChem);
    let bioSeen = 0;
    let chemSeen = 0;

    const steps = schedule.map(([day, kind]) => {
      const step = { day, date: addDays(start, day), type: kind, conditional: false, blocked: false, actions: [], products: [], warnings: [] };
      if (kind === 'cultural') {
        Object.assign(step, { title: 'Cắt bỏ, tiêu hủy phần bị bệnh', actions: [...d.cultural] });
      } else if (kind === 'biological') {
        bioSeen += 1;
        if (d.biological.length) {
          Object.assign(step, { title: 'Biện pháp sinh học' + (bioSeen > 1 ? ' (lần 2)' : ''), actions: [...d.biological] });
        } else {
          Object.assign(step, { type: 'cultural', title: 'Bổ sung biện pháp canh tác', actions: ['Chưa có chế phẩm sinh học đặc hiệu cho bệnh này.', d.cultural[1]] });
        }
      } else if (kind === 'monitor') {
        Object.assign(step, { title: 'Kiểm tra lại vườn', actions: [d.monitor, 'Chụp lại lá nghi bệnh bằng LEAF_AI để so sánh với lần chẩn đoán đầu.'] });
      } else if (kind === 'evaluate') {
        Object.assign(step, {
          title: 'Đánh giá hiệu quả',
          actions: [
            'Tiêu chí đạt: ' + d.success,
            'Nếu đạt: chuyển sang phòng ngừa, thăm vườn 1–2 lần mỗi tuần.',
            'Nếu chưa đạt: mang mẫu lá đến trạm bảo vệ thực vật để xác định lại tác nhân.'
          ]
        });
      } else {
        const prod = chems[chemSeen] || null;
        chemSeen += 1;
        const conditional = kind === 'chemical_conditional';
        Object.assign(step, {
          type: 'chemical',
          conditional,
          title: conditional ? 'Hóa học, chỉ khi bệnh vẫn lan' : 'Phun thuốc hóa học' + (nChem > 1 ? ` (lần ${chemSeen})` : ''),
          actions: [
            'Pha đúng liều ghi trên nhãn; phun ướt đều hai mặt lá, tập trung lộc non và vùng bị bệnh.',
            'Ghi nhật ký: ngày phun, tên thuốc, hoạt chất, liều lượng.'
          ],
          products: prod ? [prod] : []
        });
        if (stage === 'ra_hoa') {
          step.warnings.push('Cây đang ra hoa: không phun khi hoa nở rộ để bảo vệ ong thụ phấn; phun trước khi hoa nở hoặc sau khi hoa tàn.');
        }
        if (harvest !== null && day > harvest - guard) {
          step.blocked = true;
          step.products = [];
          step.warnings.push(`Còn dưới ${guard} ngày đến thu hoạch: không dùng thuốc hóa học, chỉ áp dụng canh tác và sinh học. Luôn kiểm tra thời gian cách ly trên nhãn.`);
        }
      }
      return step;
    });

    const liquid = Math.round(area * kb.spray_volume_l_per_m2 * 10) / 10;
    const lastDay = Math.max(...steps.map((s) => s.day));
    const notes = [d.note];
    if (harvest !== null && steps.some((s) => s.blocked)) notes.push('Có bước hóa học bị loại do gần ngày thu hoạch.');

    return {
      disease: { id: key, class: d.class, name_vi: d.name_vi, pathogen: d.pathogen, kind: d.kind },
      severity: { key: sev, ...kb.severity_levels[sev] },
      growth_stage: { key: stage, label: kb.growth_stages[stage] },
      area_m2: area,
      start_date: start,
      end_date: addDays(start, lastDay),
      duration_days: lastDay,
      days_to_harvest: harvest,
      spray: {
        liquid_l: liquid,
        tanks: Math.ceil(liquid / kb.tank_volume_l),
        tank_l: kb.tank_volume_l,
        note: 'Ước tính lượng dung dịch cho một lần phun, điều chỉnh theo độ lớn tán. Lượng thuốc pha theo nhãn.'
      },
      steps,
      monitor: d.monitor,
      success: d.success,
      notes,
      rules: GENERAL_RULES,
      source: kb.source,
      generated_by: 'offline',
      version: kb.version
    };
  }

  window.LeafTreatment = { loadKB, build, resolveDisease, resolveSeverity, todayIso, addDays };
})();
