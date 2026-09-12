const statusBox=document.getElementById('status');
async function submitJob(form){
 const buttons=[...document.querySelectorAll('button[type=submit]')];
 buttons.forEach(b=>b.disabled=true);statusBox.hidden=false;statusBox.className='status';
 statusBox.innerHTML='<strong>Working on your video</strong><p id="stage">Starting…</p><progress aria-label="Processing"></progress>';
 statusBox.scrollIntoView({behavior:'smooth',block:'nearest'});
 try{
  const response=await fetch(form.action,{method:'POST',body:new URLSearchParams(new FormData(form))});
  const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');
  for(;;){
   await new Promise(r=>setTimeout(r,1800));
   const res=await fetch('/api/jobs/'+data.id);const job=await res.json();
   if(!res.ok)throw new Error(job.error||'Cannot read progress');
   document.getElementById('stage').textContent=job.stage;
   if(job.status==='done'){location.assign('/r/'+job.slug);return;}
   if(job.status==='error')throw new Error(job.error);
  }
 }catch(error){statusBox.className='status error';statusBox.textContent=error.message;buttons.forEach(b=>b.disabled=false);}
}
document.querySelectorAll('form[data-job]').forEach(form=>form.addEventListener('submit',event=>{event.preventDefault();submitJob(form)}));
const editor=document.getElementById('post-text');
if(editor){const count=()=>document.getElementById('word-count').textContent=editor.value.trim().split(/\s+/).filter(Boolean).length+' words · 30–70 recommended';editor.addEventListener('input',count);count();}
const copy=document.getElementById('copy-caption');
if(copy)copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(document.getElementById('caption').value);copy.textContent='Copied';setTimeout(()=>copy.textContent='Copy caption',1500)}catch{copy.textContent='Select the caption to copy'}});
