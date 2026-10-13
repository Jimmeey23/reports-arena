/* Empty presentation wrappers release their space; UI chrome is not content. */
(() => {
'use strict';
const containers = '.p57-block,.p57-component,.kpi,.stat,.kpis,.statgrid,.call,.rec,.chart,figure,.rt-table-wrap,details,.p57-chapter-hero,.wrap>section,body>header';
const chrome = '.rt-table-tools,.p57-block-tools,.p57-art,.p57-marquee,.p57-hero-number,script,style';
function hasContent(el){
  const copy = el.cloneNode(true);
  copy.querySelectorAll(chrome+', [data-del-hidden], [data-p57-empty]').forEach(node=>node.remove());
  if(copy.matches('.kpi,.stat') && el.querySelector('.v,.value'))
    return [...copy.querySelectorAll('.v,.value')].some(node=>node.textContent.replace(/\u00a0/g,' ').trim());
  const visual = 'img[src],canvas,video,svg path,svg rect,svg circle,svg line,svg text,svg polygon,svg polyline,svg use';
  if(copy.matches('.chart,figure') && el.querySelector('svg,canvas,img,video,table'))
    return !!copy.querySelector(visual+',table');
  if(copy.matches('.rt-table-wrap,table'))
    return [...copy.querySelectorAll('tbody tr')].some(row=>!row.matches('.rt-total,.rt-totals') && row.querySelector('td') && row.textContent.trim());
  if(copy.matches('.call') && el.querySelector('p,ul,ol,table,figure'))
    return [...copy.querySelectorAll('p,ul,ol,table,figure')].some(node=>node.textContent.trim() || node.querySelector('svg,img,canvas'));
  if(copy.matches('details')) copy.querySelector('summary')?.remove();
  if(el.matches('.wrap>section')) copy.querySelectorAll(':scope>.p57-chapter-hero,:scope>h2,:scope>.sub').forEach(node=>node.remove());
  return !!(copy.textContent.replace(/[\u00a0\u200b]/g,' ').trim() || copy.querySelector(visual));
}
function cleanup(){
  document.querySelectorAll('.p57-block-deleted').forEach(el=>el.remove());
  document.querySelectorAll('[data-p57-empty]').forEach(el=>el.removeAttribute('data-p57-empty'));
  [...document.querySelectorAll(containers)].reverse().forEach(el=>{
    if(el.matches('th,td,tr')) return; // Blank table cells preserve the table's column structure.
    if(el.closest('.p57-monthly,.p57-atlas-monthly') && !el.matches('.p57-monthly')) return;
    if(el.closest('[data-del-hidden]')) return;
    if(el.matches('.p57-block-deleted')){el.remove();return;}
    if(!hasContent(el)) el.dataset.p57Empty='1';
  });
  document.querySelectorAll('.toc a[href^="#"],.p57-contents a[href^="#"]').forEach(link=>{
    const target=document.getElementById(link.getAttribute('href').slice(1));
    link.closest('li')?.toggleAttribute('hidden',!!target?.closest('[data-del-hidden],[data-p57-empty]'));
  });
}
function component(el){return el.closest('.p57-monthly,.kpi,.stat,.chart,figure,.rt-table-wrap,.rec,.call,.p57-chapter-hero') || el;}
window.P57EditModel={hasContent,cleanup,component};
})();
