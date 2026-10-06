/**
 * LEAF_AI — Chi tiết bệnh (disease.html?id=anthracnose)
 */
(function () {
  'use strict';
  const { diseases, sevBadge, escapeHtml, params } = window.Leaf;
  const $ = (id) => document.getElementById(id);

  const list = diseases.list();
  const d = diseases.find(params.get('id')) || list[0];
  const idx = list.indexOf(d);

  const shortName = d.name_vi.split(' (')[0];
  document.title = `${d.name_vi} — LEAF_AI`;
  $('crumbName').textContent = shortName;
  $('dName').textContent = d.name_vi;
  $('dLatin').textContent = `${d.name_en}, tác nhân ${d.pathogen}`;
  $('dMeta').innerHTML = `${sevBadge(d.severity_default)}
    <span class="tag">${diseases.kind(d)}</span>
    <span class="tag">Nhận diện: ${diseases.models(d)}</span>`;
  $('dLead').textContent = d.symptoms.stage_2;
  $('dImg').src = d.thumb;
  $('dImg').alt = `Minh hoạ lá vải bị ${shortName.toLowerCase()}`;
  $('dTreat').href = `treatment.html?id=${d.id}`;
  $('dTreat2').href = `treatment.html?id=${d.id}`;
  $('dAsk').onclick = () => window.Leaf?.openChat(`Cách xử lý ${shortName.toLowerCase()} trên cây vải theo hướng IPM?`);

  const stages = [
    ['Khởi phát', d.symptoms.stage_1],
    ['Phát triển', d.symptoms.stage_2],
    ['Bùng phát', d.symptoms.stage_3]
  ];
  $('dStages').innerHTML = stages.map(([t, s], i) => `
    <li><b>${i + 1}</b><div><h3>${t}</h3><p>${escapeHtml(s)}</p></div></li>`).join('');

  $('dConditions').textContent = d.conditions;
  $('dPrevention').textContent = d.prevention;
  $('tCultural').textContent = d.treatment.cultural;
  $('tBio').textContent = d.treatment.biological;
  $('tChem').textContent = d.treatment.chemical;
  $('dRefs').textContent = `Nguồn: ${d.references}`;

  $('dOthers').innerHTML = list.map((x) => `
    <li><a href="disease.html?id=${x.id}"${x === d ? ' aria-current="page"' : ''}>
      <span class="dot" style="--dot:${x.color}"></span>${escapeHtml(x.name_vi.split(' (')[0])}
    </a></li>`).join('');

  const prev = list[(idx - 1 + list.length) % list.length];
  const next = list[(idx + 1) % list.length];
  $('dPager').innerHTML = `
    <a class="btn btn-ghost" href="disease.html?id=${prev.id}"><i class="bi bi-arrow-left"></i>${escapeHtml(prev.name_vi.split(' (')[0])}</a>
    <a class="btn btn-ghost" href="disease.html?id=${next.id}">${escapeHtml(next.name_vi.split(' (')[0])}<i class="bi bi-arrow-right"></i></a>`;
})();
