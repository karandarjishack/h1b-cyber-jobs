import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";
const html=fs.readFileSync("docs/tracker.html","utf8");
const script=html.split("<script>")[1]?.split("</script>")[0];
assert.ok(script,"Tracker must have executable JS");
assert.ok(html.includes('class="board"') && html.includes('function render()'),"Tracker renders dynamic Kanban lanes");
const nodes=new Map();
function el(id){
 if(!nodes.has(id)){
  const item={id,value:"",textContent:"",innerHTML:"",style:{},dataset:{},files:[],focus(){},click(){},
    addEventListener(){},setAttribute(){},classList:{add(){},remove(){},contains(){return false;}}};
  nodes.set(id,item);
 }
 return nodes.get(id);
}
const storage=new Map();
const context=vm.createContext({
 document:{getElementById:el,addEventListener(){},querySelectorAll(){return []},activeElement:null,body:{style:{}},createElement(){return {click(){},remove(){}}}},
 localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,String(v))},
 navigator:{clipboard:{writeText:async()=>{}}},
 URL,Blob,Date,JSON,Map,Set,setTimeout,clearTimeout,console
});
new vm.Script(script,{filename:"tracker.html"}).runInContext(context);
const run=s=>vm.runInContext(s,context);
assert.ok(run('STAGES.join(",")')==="Saved,Applied,Interview,Offer,Rejected","Expected Kanban status columns");
assert.equal(run('tracked().filter(x=>x.status==="Applied").length'),1,"Known applied role preserved");
assert.ok(el("board").innerHTML.includes("Cybersecurity Analyst"),"A previously applied record renders");
run('state.records["sample"]={status:"Saved",date:"",notes:"",updated_at:"2026-11-16",snap:{title:"<img src=x onerror=alert(1)>",employer:"Test & Co",location:"Remote, US",url:"javascript:alert(1)",fit:"90",ev:"C",keywords:[]}};render()');
const cards=el("board").innerHTML;
assert.ok(cards.includes("&lt;img"),"Job title escaped");
assert.ok(!cards.includes("<img"),"No HTML injected");
run('move("sample","Interview")');
assert.equal(run('state.records["sample"].status'),"Interview","Moving a job changes stage");
run('move("sample","Applied")');
assert.equal(run('state.records["sample"].status'),"Applied","Move to Applied works");
const safe=run('record({status:"Saved",snap:{title:"Testing",employer:"Co",url:"javascript:alert(1)"}})');
assert.equal(safe.snap.url,"","Unsafe URLs stripped");
const backup=JSON.stringify({tracker:{"ext-new":{status:"Offer",date:"2026-11-16",snap:{title:"Security Engineer",employer:"Example",url:"https://example.com/apply"}},"__proto__":{status:"Saved"},"bad":{status:"SUPER"}}});
const amount=run('restore('+JSON.stringify(JSON.parse(backup))+')');
assert.ok(amount>=1,"Tracker backup restored valid item");
assert.equal(run('state.records["ext-new"].status'),"Offer");
assert.equal(run('state.records["sample"].status'),"Applied","Existing statuses win over imported values");
assert.ok(el("board").innerHTML.includes("Security Engineer"),"Imported job displays");
const dashboard=fs.readFileSync("docs/board-v2.html","utf8");
assert.ok(dashboard.includes('id="scan-now"'),"Manual scan button present");
assert.ok(dashboard.includes("issues/new?title=Run%20CyberJobs%20scan"),"Scan button opens authenticated issue");
const workflow=fs.readFileSync(".github/workflows/daily.yml","utf8");
assert.ok(workflow.includes("issues:")&&workflow.includes("types: [opened]"));
assert.ok(workflow.includes("github.event.issue.user.login == 'karandarjishack'"),"Only owner can run through issues");
assert.ok(workflow.includes("github.event.issue.title == 'Run CyberJobs scan'"),"Title exact-match");
assert.ok(workflow.includes("gh issue close"),"Run request issue is automatically closed");
console.log("PASS tracker Kanban rendering, drag status, backup import, XSS protection, owner-only manual run action");
