// n8n Code node body for "Build Verified UFC Card" in UFC | svc.populate_fight_card (parser_version ufc-fight-card-v3).
// Copied unchanged from the 2026-10-27 operator handoff. Not yet applied or published in n8n.
const HEADERS=['fight_order','fighter_a','fighter_b','fighter_a_aliases','fighter_b_aliases','bout_type','scheduled_rounds','weight_class'];
const text=v=>String(v??'').trim();
const norm=v=>text(v).normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
const cleanName=v=>text(v).replace(/\s*\[https?:\/\/[^\]]+\]/g,'').replace(/\s+/g,' ').trim();
const populated=rows=>(rows||[]).slice(1).filter(row=>row.some(v=>text(v)));
function checkCard(rows,allowEmpty=false){
 if(!Array.isArray(rows)||HEADERS.some((h,i)=>text(rows[0]?.[i])!==h))throw new Error('Fight Card needs the eight expected headers in columns A:H.');
 const data=populated(rows);
 if(!data.length){if(allowEmpty)return [];throw new Error('Fight Card is empty. Run UFC event spreadsheet setup before analysis.');}
 const seen=new Set();
 data.forEach((r,i)=>{
  if(Number(r[0])!==i+1||!text(r[1])||!text(r[2])||norm(r[1])===norm(r[2]))throw new Error('Fight Card has invalid order or fighters at fight '+(i+1)+'.');
  if(!['main_event','main_card','prelim'].includes(text(r[5]))||![3,5].includes(Number(r[6])))throw new Error('Fight Card has missing bout type or scheduled rounds at fight '+(i+1)+'.');
  if((i===0)!==(r[5]==='main_event'))throw new Error('Fight Card must have exactly one main event at fight 1.');
  if(!text(r[7]))throw new Error('Fight Card is missing weight_class at fight '+(i+1)+'.');
  for(const name of [r[1],r[2]]){const key=norm(name);if(seen.has(key))throw new Error('Fight Card contains a duplicate fighter: '+name);seen.add(key);}
 });
 return data;
}
function fingerprint(rows){const value=JSON.stringify(rows.map(r=>r.map(v=>text(v))));let hash=2166136261;for(let i=0;i<value.length;i++)hash=Math.imul(hash^value.charCodeAt(i),16777619)>>>0;return 'fnv1a-'+hash.toString(16).padStart(8,'0');}
// UFC.com and ESPN spell first names differently (Zachary/Zach, Joseph/Joe), so fighters match on surname plus first initial.
const nameTokens=v=>text(v).normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/['’.]/g,'').split(/[^a-z0-9]+/).filter(Boolean);
const fighterKey=v=>{const t=nameTokens(v);return t.length?t[0][0]+':'+t[t.length-1]:'';};
const pair=(a,b)=>[fighterKey(a),fighterKey(b)].sort().join('|');
const espnPair=c=>c.competitors?.length===2?pair(c.competitors[0].athlete?.displayName,c.competitors[1].athlete?.displayName):'';
const espnNames=c=>(c.competitors||[]).map(x=>x.athlete?.displayName||'?').join(' vs ');

const event=$('Prepare UFC Card Request').first().json;
const official=$('Extract Official UFC Card').first().json;
const http=$('Fetch Official UFC Card').first().json;
if(http.statusCode!==200)throw new Error('Official UFC card request returned HTTP '+http.statusCode+'. No spreadsheet data was written.');
if(String(official.canonical||'').replace(/\/$/,'')!==event.source_url)throw new Error('Official UFC page does not match the stored event URL.');
if(Math.abs(Number(official.main_timestamp)*1000-Date.parse(event.event_datetime_local))>18*3600000||!Number(official.main_timestamp))throw new Error('Official UFC card date does not match the selected event.');
// UFC.com lists every bout in one running order (main event first) without card sections.
const arrays=['fight_ids','fight_a','fight_b','fight_a_url','fight_b_url'].map(k=>official[k]);
if(arrays.some(a=>!Array.isArray(a))||arrays.some(a=>a.length!==arrays[0].length))throw new Error('Official UFC card fields are incomplete.');
const card=arrays[0].map((id,i)=>({bout_id:'ufc:'+id,fighter_a:cleanName(arrays[1][i]),fighter_b:cleanName(arrays[2][i]),fighter_a_url:arrays[3][i],fighter_b_url:arrays[4][i]}));
if(card.length<2||card.length>30||new Set(card.map(b=>b.bout_id)).size!==card.length)throw new Error('Official UFC card is missing, duplicated or outside the expected size.');
const response=$input.first().json;
if(response.statusCode!==200)throw new Error('ESPN round verification returned HTTP '+response.statusCode+'. No spreadsheet data was written.');
const firstPair=pair(card[0].fighter_a,card[0].fighter_b);
const options=(response.body?.events||[]).filter(e=>Math.abs(Date.parse(e.date)-Date.parse(event.event_datetime_local))<=24*3600000&&(e.competitions||[]).some(c=>espnPair(c)===firstPair));
if(options.length!==1)throw new Error('Could not uniquely verify this UFC event and its main event on ESPN.');
const espn=options[0];
const competitions=(espn.competitions||[]).filter(c=>!/cancel|postpon/i.test(String(c.status?.type?.name||'')));
const used=new Set();
for(const bout of card){
 const matches=competitions.filter(c=>espnPair(c)===pair(bout.fighter_a,bout.fighter_b));
 if(matches.length!==1||used.has(matches[0].id))throw new Error('Could not verify pairing and rounds for '+bout.fighter_a+' vs '+bout.fighter_b+'.');
 const comp=matches[0];used.add(comp.id);
 const rounds=Number(comp.format?.regulation?.periods);
 if(![3,5].includes(rounds))throw new Error('Scheduled rounds are unavailable for '+bout.fighter_a+' vs '+bout.fighter_b+'.');
 const weightClass=String(comp.type?.abbreviation||'').trim().toLowerCase();
 if(!/^[a-z][a-z '’-]{3,39}$/.test(weightClass))throw new Error('Weight class is unavailable for '+bout.fighter_a+' vs '+bout.fighter_b+'.');
 Object.assign(bout,{fight_order:card.indexOf(bout)+1,scheduled_rounds:rounds,weight_class:weightClass,espn_competition_id:String(comp.id),espn_start:String(comp.date||''),fighter_a_aliases:'',fighter_b_aliases:''});
 for(const key of ['fighter_a_url','fighter_b_url'])if(!/^https:\/\/www\.ufc\.com\/athlete\/[a-z0-9-]+$/.test(bout[key]))throw new Error('Invalid official athlete URL.');
}
// UFC.com no longer marks card sections: ESPN's latest start time sizes the main card, applied to UFC.com's running order.
const latest=Math.max(...card.map(b=>Date.parse(b.espn_start)).filter(Number.isFinite));
const mainCardSize=card.filter(b=>Date.parse(b.espn_start)===latest).length;
if(!Number.isFinite(latest)||mainCardSize<1)throw new Error('ESPN start times are unavailable, so the main card cannot be sized.');
const warnings=[];
card.forEach((b,i)=>{
 b.bout_type=i===0?'main_event':(i<mainCardSize?'main_card':'prelim');
 const espnMain=Date.parse(b.espn_start)===latest;
 if(espnMain!==(i<mainCardSize))warnings.push('ESPN lists '+b.fighter_a+' vs '+b.fighter_b+' on the '+(espnMain?'main card':'prelims')+'; UFC.com order puts it on the '+(i<mainCardSize?'main card':'prelims')+'.');
 delete b.espn_start;
});
for(const c of competitions)if(!used.has(c.id))warnings.push('ESPN also lists '+espnNames(c)+', which is not on the UFC.com card. It was left out.');
const rows=card.map(b=>HEADERS.map(h=>b[h]));
checkCard([HEADERS,...rows]);
return [{json:{...event,card,warnings,espn_event_id:String(espn.id),source_fingerprint:fingerprint(rows),parser_version:'ufc-fight-card-v3',checked_at:new Date().toISOString()}}];
