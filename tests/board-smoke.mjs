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
 "research/latest.json":JSON.parse(fs.readFileSync("docs/research/latest.json","utf8"))
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
assert.ok(counted>=formerlyRecent.length,"Last seven days must include "+formerlyRecent.length+" prior catalog records; got "+counted);
assert.equal(evalIn('displayed().length'),counted,"Latest tab must show all recent records");
assert.ok(evalIn('all().length')>=datasets["history.json"].length,"All-jobs index keeps prior records");
assert.equal(evalIn('tr()["jrm-cyber-analyst-nyc-2026-11-13"]?.status'),"Applied","Previously confirmed application restored");
evalIn('state.view="my"');
assert.ok(evalIn('displayed().some(x=>x.id==="jrm-cyber-analyst-nyc-2026-11-13")'),"Applied job visible in My Applications");
evalIn('state.view="all"');
assert.equal(evalIn('displayed().length'),evalIn('allTracked().length'),"All jobs tab shows entire catalog");
const rows=evalIn('displayed().map(x=>x.id)');
assert.ok(rows.length>0,"Not an empty job board");
console.log("PASS: historical="+datasets["history.json"].length+" prior_last_7="+formerlyRecent.length+" latest="+counted+" all="+rows.length+" applied_restore=true");
