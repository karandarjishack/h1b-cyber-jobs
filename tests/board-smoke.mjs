// Dependency-free browser-view smoke test, using real saved GitHub data files.
import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";
const page=fs.readFileSync("docs/board-v2.html","utf8");
const script=page.split("<script>")[1]?.split("</script>")[0];
assert.ok(script,"Embedded job-board JavaScript exists");
const datasets={
 "daily.json":JSON.parse(fs.readFileSync("docs/daily.json","utf8")),
 "history.json":JSON.parse(fs.readFileSync("docs/history.json","utf8")),
 "research/latest.json":JSON.parse(fs.readFileSync("docs/research/latest.json","utf8")),
 "research/exclusions.json":JSON.parse(fs.readFileSync("docs/research/exclusions.json","utf8"))
};
const nodes=new Map();
const elem=id=>{
 if(!nodes.has(id)){
  nodes.set(id,{
   id,style:{},value:"",textContent:"",innerHTML:"",
   addEventListener(){},setAttribute(){},focus(){},
   classList:{add(){},remove(){},toggle(){}}
  });
 }
 return nodes.get(id);
};
const storage=new Map();
const localStorage={
 getItem:k=>storage.has(k)?storage.get(k):null,
 setItem:(k,v)=>storage.set(k,String(v)),
 removeItem:k=>storage.delete(k)
};
const document={getElementById:elem,querySelectorAll:()=>[],addEventListener(){},body:{style:{}}};
const fetch=async src=>{
 const name=String(src).split("?")[0];
 return {ok:Object.prototype.hasOwnProperty.call(datasets,name),json:async()=>datasets[name]};
};
const context=vm.createContext({document,fetch,localStorage,URL,Date,Promise,setTimeout,clearTimeout,console,Blob,window:{},navigator:{}});
new vm.Script(script,{filename:"board-v2.html"}).runInContext(context);
await new Promise(resolve=>setTimeout(resolve,45));
const evalIn=expr=>vm.runInContext(expr,context);
assert.equal(evalIn("state.history.length"),datasets["history.json"].length,"Entire historical catalog loaded");
const d=datasets["daily.json"];
const formerlyRecent=datasets["history.json"].filter(j=>j.posted&&j.posted>=d.window.from&&j.posted<=d.window.to);
const counted=evalIn("recent().length");
const excludes=datasets["research/exclusions.json"].exclusions;
const includedOld=formerlyRecent.filter(j=>!excludes.some(x=>x.employer.toLowerCase()===String(j.employer||"").toLowerCase()&&x.title.toLowerCase()===String(j.title||"").toLowerCase()));
assert.ok(counted>=includedOld.length,"Last seven days must retain all non-excluded earlier records");
assert.ok(evalIn('recent().every(x=>!disqualified(x))'),"Evidence-confirmed ineligible jobs must be removed from Latest");
assert.equal(evalIn('displayed().length'),counted,"Latest tab must show all recent records");
assert.ok(evalIn('all().length')>=datasets["history.json"].length-excludes.length,"All-jobs keeps all historically eligible records");
assert.equal(evalIn('tr()["jrm-cyber-analyst-nyc-2026-11-13"]?.status'),"Applied","Previously confirmed application restored");
evalIn('state.view="my"');
assert.ok(evalIn('displayed().some(x=>x.id==="jrm-cyber-analyst-nyc-2026-11-13")'),"Applied job visible in My Applications");
evalIn('state.view="all"');
assert.equal(evalIn('displayed().length'),evalIn('allTracked().length'),"All jobs tab shows entire catalog");
const rows=evalIn('displayed().map(x=>x.id)');
assert.ok(rows.length>0,"Not an empty job board");
// Imported tracker must be schema-checked, prevent script URLs and preserve existing statuses.
const fixture={tracker:{"safe-job":{status:"Applied",date:"2026-11-15",notes:"test",snap:{title:"Role",employer:"Example",url:"javascript:alert(1)"}},
"__proto__":{status:"Applied"},"unsafe":{status:"Definitely Hired"},"pending":{status:"Saved"}}};
const imported=evalIn("safeImportTracker("+JSON.stringify(JSON.stringify(fixture))+")");
assert.equal(imported["safe-job"].status,"Applied","Valid import records retain status");
assert.equal(imported["safe-job"].snap.url,"","Untrusted application links are dropped");
assert.equal(imported.unsafe,undefined,"Unknown statuses are rejected");
assert.equal(imported.pending.status,"Saved","Saved state imports cleanly");
const sample=evalIn('renderRow({id:"x",employer:"Test",title:"<img src=x onerror=alert(1)>",location:"Remote, United States",posted:"2026-11-14",fit_score:77,keywords_matched:[],sponsorship_evidence:"C_ask_recruiter",review_reasons:["check"]})');
assert.ok(sample.includes("&lt;img"),"Job title HTML must be escaped");
assert.ok(!sample.includes("<img"),"Injected tags never enter job markup");
const managerless=evalIn('recent().find(x=>!x.hiring_manager_name)?.id');
if(managerless){
 evalIn("show("+JSON.stringify(managerless)+")");
 const detail=nodes.get("drawer").innerHTML;
 assert.ok(detail.includes("Search hiring team on LinkedIn"),"Every managerless job offers a public contact research action");
 assert.ok(detail.includes("No verified exact-job LinkedIn post"),"No invented hiring post");
 evalIn("hide()");
}
evalIn('state.view="latest";state.strongOnly=true');
assert.ok(evalIn('displayed().every(x=>Number(x.fit_score||0)>=75)'),"Strong-fit filter only shows 75+ matches");
evalIn('state.strongOnly=false');
console.log("PASS: historical="+datasets["history.json"].length+" prior_last_7="+formerlyRecent.length+" latest="+counted+" all="+rows.length+" applied_restore=true");
