() => {
 const svg=document.querySelector('svg');
 const all=[...svg.querySelectorAll('*')];
 const order=new Map(all.map((e,i)=>[e,i]));
 const rootInv=svg.getCTM().inverse();
 function matrix(e){return rootInv.multiply(e.getCTM());}
 function point(m,x,y){const p=new DOMPoint(x,y).matrixTransform(m);return [p.x,p.y];}
 function bbox(e){let b=e.getBBox(),m=matrix(e);let ps=[[b.x,b.y],[b.x+b.width,b.y],[b.x+b.width,b.y+b.height],[b.x,b.y+b.height]].map(p=>point(m,...p));let xs=ps.map(p=>p[0]),ys=ps.map(p=>p[1]);return [Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)];}
 function intersect(a,b,r){let t0=0,t1=1;const dx=b[0]-a[0],dy=b[1]-a[1];for(const [p,q] of [[-dx,a[0]-r[0]],[dx,r[2]-a[0]],[-dy,a[1]-r[1]],[dy,r[3]-a[1]]]){if(Math.abs(p)<1e-9){if(q<0)return null;}else{const t=q/p;if(p<0)t0=Math.max(t0,t);else t1=Math.min(t1,t);if(t0>t1)return null;}}return [[a[0]+t0*dx,a[1]+t0*dy],[a[0]+t1*dx,a[1]+t1*dy]];}
 const masks=all.filter(e=>e.tagName==='rect' && ['rgb(255, 255, 255)','white','#ffffff'].includes(getComputedStyle(e).fill) && getComputedStyle(e).fillOpacity==='1' && getComputedStyle(e).opacity==='1').map(e=>({box:bbox(e),z:order.get(e),role:e.getAttribute('data-role')}));
 const shapes=all.filter(e=>['path','polyline','polygon','line','rect','ellipse','circle'].includes(e.tagName) && getComputedStyle(e).stroke!=='none' && +getComputedStyle(e).strokeOpacity>0 && parseFloat(getComputedStyle(e).strokeWidth)>0);
 let segments=[];
 for(const e of shapes){const m=matrix(e);const len=e.getTotalLength();let n=Math.max(1,Math.ceil(len/.75));let prev=e.getPointAtLength(0);for(let k=1;k<=n;k++){const next=e.getPointAtLength(len*k/n);segments.push({a:point(m,prev.x,prev.y),b:point(m,next.x,next.y),z:order.get(e),shape:all.indexOf(e),role:e.getAttribute('data-role')||e.getAttribute('data-cell-id')||e.tagName});prev=next;}}
 function inkbox(e){
  const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d'),m=matrix(e),boxes=[];
  const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let offset=0,node;
  while(node=walker.nextNode()){
   const st=getComputedStyle(node.parentElement);ctx.font=`${st.fontStyle} ${st.fontWeight} ${st.fontSize} ${st.fontFamily}`;
   for(const ch of node.textContent){
    if(offset>=e.getNumberOfChars())break;
    const p=e.getStartPositionOfChar(offset),b=ctx.measureText(ch);offset+=ch.length;
    if(!ch.trim())continue;
    const ps=[[p.x-b.actualBoundingBoxLeft,p.y-b.actualBoundingBoxAscent],[p.x+b.actualBoundingBoxRight,p.y+b.actualBoundingBoxDescent]].map(p=>point(m,...p));boxes.push(...ps);
   }
  }
  return boxes.length?[Math.min(...boxes.map(p=>p[0])),Math.min(...boxes.map(p=>p[1])),Math.max(...boxes.map(p=>p[0])),Math.max(...boxes.map(p=>p[1]))]:bbox(e);
 }
 const texts=all.filter(e=>e.tagName==='text' && e.textContent.trim()).map((e,i)=>({index:i,text:e.textContent,box:inkbox(e),z:order.get(e)}));
 const collisions=[];
 for(const t of texts){const box=t.box.map((v,i)=>v+(i<2?-1:1));let hits=new Map();for(const s of segments){let pts=intersect(s.a,s.b,box);if(!pts)continue;let hidden=masks.some(m=>m.z>s.z && m.z<t.z && pts.every(p=>p[0]>=m.box[0]-.01&&p[0]<=m.box[2]+.01&&p[1]>=m.box[1]-.01&&p[1]<=m.box[3]+.01));if(!hidden)hits.set(s.shape,{shape:s.shape,role:s.role,point:pts[0]});}if(hits.size)collisions.push({...t,hits:[...hits.values()]});}
 window._labelGeometry={all,order,matrix,bbox,inkbox,intersect,masks,segments,texts};
 return {text_count:texts.length,shape_count:shapes.length,segment_count:segments.length,collisions,texts};
}
