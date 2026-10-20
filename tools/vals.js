// usage: node vals.js page.dc.html -> prints renderVals() JSON using data-props defaults
const fs=require('fs');
const s=fs.readFileSync(process.argv[2],'utf8');
const m=s.match(/<script type="text\/x-dc"[^>]*data-props='([^']*)'[^>]*>([\s\S]*?)<\/script>/);
const props={}; const dp=JSON.parse(m[1]);
for(const k in dp){ if(k[0]!=='$' && dp[k] && 'default' in dp[k]) props[k]=dp[k].default; }
const code=`class DCLogic{constructor(p){this.props=p}}\n${m[2]}\n;new Component(props).renderVals()`;
const vals=new Function('props','return eval(arguments[1])')(props,code);
process.stdout.write(JSON.stringify(vals));
