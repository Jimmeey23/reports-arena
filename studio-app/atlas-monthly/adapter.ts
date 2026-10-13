type Definition = {label:string; description:string; unit:string; higherIsBetter?:boolean};
const definitions = new Map<string,Definition>();
export const register = (items: Record<string, Definition>) => Object.entries(items).forEach(([id,d])=>definitions.set(id,d));
export const definition = (id:string) => definitions.get(id);
export function reportFmt(id:string,value:unknown) {
  if(value == null) return 'Unavailable';
  if(typeof value !== 'number') return String(value);
  const unit=definition(id)?.unit||'';
  const digits=unit==='₹'?0:unit==='%'||unit==='pp'?1:2;
  const text=value.toLocaleString('en-IN',{minimumFractionDigits:digits===1?1:0,maximumFractionDigits:digits});
  if(unit==='₹') return '₹'+text;
  if(unit==='pp') return `${value>0?'+':''}${text} pp`;
  return text+(unit==='%'||unit==='×'?unit:unit?' '+unit:'');
}
export function reportDelta(id:string,value:unknown,prior:unknown) {
  if(typeof value!=='number'||typeof prior!=='number') return '—';
  const difference=value-prior;
  if(['%','pp'].includes(definition(id)?.unit??'')) return `${difference>=0?'+':''}${difference.toFixed(1)} pp`;
  if(prior===0) return difference===0?'0%':'—';
  const percent=difference/Math.abs(prior)*100;
  return `${percent>=0?'+':''}${percent.toFixed(1)}%`;
}
export function exportCSV(name:string,rows:Record<string,unknown>[]) {
  const keys=[...new Set(rows.flatMap(r=>Object.keys(r)))];
  const quote=(value:unknown)=>{let s=String(value??'');if(/^[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
  const csv=[keys,...rows.map(r=>keys.map(k=>r[k]))].map(row=>row.map(quote).join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download=name+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
