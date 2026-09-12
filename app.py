"""Local content studio. Run python app.py, then open http://localhost:8000."""
from __future__ import annotations
import html
import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse, unquote
from make import ROOT, run
from video import catalogue, render_mp4
OUT=ROOT/'out'
POOL=ThreadPoolExecutor(max_workers=1)
JOBS={}
LOCK=threading.Lock()
e=html.escape

def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default

def brand_dir(slug):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*',slug):
        raise ValueError('Invalid brand')
    path=OUT/slug
    if not (path/'post.md').is_file():
        raise ValueError('Brand not found')
    return path

def saved_post(d):
    final=read_json(d/'final.json')
    if final:return final
    text=next((line[2:] for line in (d/'post.md').read_text(encoding='utf-8').splitlines() if line.startswith('> ')), '')
    scores={s['id']:s for s in read_json(d/'scores.json',[])}
    variants=read_json(d/'variants.json',[])
    winner=max(variants,key=lambda v:scores.get(v['id'],{}).get('overall',0)) if variants else {}
    return {**winner,'text':text}

def gallery():
    cards=[]
    for d in sorted(OUT.iterdir()):
        if d.name.startswith('_') or not (d/'post.md').exists():continue
        profile=read_json(d/'profile.json',{})
        image=d/'post.png'
        stamp=image.stat().st_mtime_ns if image.exists() else 0
        cards.append(f'<a class="project" href="/r/{d.name}"><img loading="lazy" src="/out/{d.name}/post.png?v={stamp}" alt="{e(profile.get("brand_name",d.name))} video preview"><strong>{e(profile.get("brand_name",d.name))}</strong><small>{e(profile.get("niche",""))}</small></a>')
    return '<section class="gallery"><div class="gallery-head"><h2>Made in the studio</h2><span class="muted">'+str(len(cards))+' examples</span></div><div class="gallery-grid">'+''.join(cards)+'</div></section>'

def result_html(slug):
    d=brand_dir(slug);final=saved_post(d);profile=read_json(d/'profile.json',{});meta=read_json(d/'post.video.json',{})
    text=final['text'];clip=meta.get('clip');stamp=(d/'post.mp4').stat().st_mtime_ns if (d/'post.mp4').exists() else 0
    choices=[]
    for name,info in sorted(catalogue().items(),key=lambda item:(item[1].get('collection')!='reaction',item[1].get('name',''))):
        if not (ROOT/'base'/name).is_file():continue
        checked='checked' if name==clip else ''
        choices.append(f'<label class="clip"><input type="radio" name="clip" value="{e(name)}" {checked}><span class="tile"><img src="/base/{e(Path(name).stem)}.jpg" alt=""><span class="name">{e(info.get("name",name))}</span><span class="mood">{e(info.get("mood",""))}</span></span></label>')
    variants=read_json(d/'variants.json',[])
    alternatives=''.join('<li>'+e(v['text'])+'</li>' for v in variants if v.get('text')!=text)
    source=f'<a href="{e(meta["source"])}" target="_blank" rel="noreferrer">Clip source ↗</a>' if meta.get('source') else 'Local stock library'
    return f'''
<section class="workspace">
 <div class="preview"><video class="player" src="/out/{slug}/post.mp4?v={stamp}" poster="/out/{slug}/post.png?v={stamp}" controls autoplay muted loop playsinline></video>
 <div class="preview-meta"><span>1080 × 1920 · MP4</span><span>{meta.get('duration_s','—')}s · silent</span></div>
 <div class="actions"><a class="button" download="{slug}.mp4" href="/out/{slug}/post.mp4">Download video ↓</a><a class="button secondary" href="/out/{slug}/post.md">Post notes</a></div>
 <p class="footnote">{e(meta.get('name',meta.get('reaction','Reaction')) or 'Reaction')} · {source}</p></div>
 <div><span class="badge">{e(profile.get('niche','Brand'))}</span><span class="badge">Reaction + text</span>
 <h2>{e(profile.get('brand_name',slug))}</h2><p class="muted">{e(profile.get('one_liner',''))}</p>
 <form action="/api/render" method="post" data-job><input type="hidden" name="slug" value="{slug}">
 <div class="field"><label for="post-text">The story</label><textarea id="post-text" name="text" required maxlength="900">{e(text)}</textarea><small id="word-count"></small></div>
 <div class="field"><label for="caption">Caption</label><input id="caption" name="caption" maxlength="300" value="{e(final.get('caption','') or '')}"></div>
 <h3>Choose the reaction</h3><div class="clip-grid">{''.join(choices)}</div>
 <p class="footnote">Change the clip or words. Rebuilding uses your saved post, with no AI writing call.</p>
 <div class="actions"><button type="submit">Rebuild video</button><button type="button" id="copy-caption" class="secondary">Copy caption</button></div></form>
 <details><summary>Why this post?</summary><p>{e(final.get('why_this_brand',''))}</p><p><strong>Audience:</strong> {e(str(profile.get('audience','')))}</p><p><strong>Brand context:</strong> {e(str(profile.get('core_pain','')))}</p><p class="muted">Draft scores are AI editorial judgments, not measured audience results. Exports have no audio track.</p></details>
 <details><summary>Other writing directions</summary><ul class="alternatives">{alternatives}</ul></details>
 </div></section>'''

def page(slug=None):
    body=result_html(slug) if slug else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Frame — Content studio</title><link rel="stylesheet" href="/static/studio.css"></head>
<body><div class="shell"><header><a class="logo" href="/"><span></span>FRAME</a><span class="topnote">Brand URL → a finished video</span></header>
<section class="hero"><div class="eyebrow">Short-form content studio</div><h1>A brand. A point of view.</h1><p>Turn a website into a sharp story and a familiar reaction.</p></section>
<form class="url-form" action="/api/make" method="post" data-job><label for="brand-url" class="sr-only">Brand website</label><input id="brand-url" name="url" placeholder="Paste a brand website, e.g. duolingo.com" required><button type="submit">Create a video ↗</button></form>
<div id="status" class="status" role="status" aria-live="polite" hidden></div>{body}{gallery()}
<footer>Personal demo · Curated reactions + editable content · Built for a human editor</footer></div><script src="/static/studio.js"></script></body></html>'''

def rebuild(payload, progress):
    slug=payload.get('slug','');d=brand_dir(slug);final=saved_post(d)
    text=payload.get('text',final['text']).strip();caption=payload.get('caption',final.get('caption','')).strip()
    if not 15<=len(text.split())<=90:raise ValueError('Use 15–90 words; 30–70 works best for this format.')
    if len(text)>900 or len(caption)>300:raise ValueError('The text or caption is too long.')
    profile=read_json(d/'profile.json',{})
    progress('Rendering your selected reaction and text')
    _,how=render_mp4(text,d/'post.mp4',profile.get('brand_name',slug),reaction=final.get('reaction'),clip_name=payload.get('clip') or None)
    md=(d/'post.md').read_text(encoding='utf-8')
    lines=md.splitlines();replaced=False
    for i,line in enumerate(lines):
        if line.startswith('> ') and not replaced:lines[i]='> '+text.replace('\n',' ');replaced=True
        if line.startswith('**Caption:**'):lines[i]='**Caption:** '+caption
    (d/'post.md').write_text('\n'.join(lines),encoding='utf-8')
    final.update(text=text,caption=caption,video=how,edited_by_user=True,selected_clip=payload.get('clip') or None)
    (d/'final.json').write_text(json.dumps(final,indent=2,ensure_ascii=False),encoding='utf-8')
    return slug

def start_job(kind,payload):
    with LOCK:
        if any(j['status']=='running' for j in JOBS.values()):raise ValueError('A video is already being prepared. Please let it finish first.')
        job_id=uuid.uuid4().hex
        JOBS[job_id]={'status':'running','stage':'Starting','created':time.time()}
    def progress(stage):
        with LOCK:JOBS[job_id]['stage']=stage
    def work():
        try:
            if kind=='make':
                url=payload.get('url','').strip()
                if not url.startswith(('http://','https://')):url='https://'+url
                parsed=urlparse(url)
                if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username:raise ValueError('Enter a valid brand website address.')
                result=run(url,progress=progress);slug=result['slug']
            else:slug=rebuild(payload,progress)
            with LOCK:JOBS[job_id].update(status='done',stage='Video ready',slug=slug)
        except Exception as error:
            print('Job failed:',type(error).__name__,str(error),flush=True)
            with LOCK:JOBS[job_id].update(status='error',stage='Needs attention',error=str(error))
    POOL.submit(work)
    return job_id

class H(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def json_response(self,data,status=200):
        body=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def file_response(self,path):
        size=path.stat().st_size;start,end=0,size-1;partial=False
        if self.headers.get('Range'):
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',self.headers['Range'])
            if not match:self.send_error(416);return
            a,b=match.groups()
            if a:start=int(a);end=min(int(b),end) if b else end
            elif b:start=max(0,size-int(b))
            else:self.send_error(416);return
            if start>end or start>=size:self.send_error(416);return
            partial=True
        self.send_response(206 if partial else 200)
        self.send_header('Content-Type',self.guess_type(str(path)));self.send_header('Accept-Ranges','bytes')
        self.send_header('Content-Length',str(end-start+1));self.send_header('Cache-Control','no-cache')
        if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        if self.command=='HEAD':return
        # Close the Windows file handle before sending to a slow video client.
        with path.open('rb') as stream:
            stream.seek(start)
            content=stream.read(end-start+1)
        try:
            self.wfile.write(content)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
    def do_GET(self):
        url=urlparse(self.path);route=unquote(url.path)
        if route.startswith('/api/jobs/'):
            with LOCK:job=dict(JOBS.get(route.rsplit('/',1)[-1],{}))
            return self.json_response(job if job else {'error':'Job not found'},200 if job else 404)
        if route=='/' or route.startswith('/r/'):
            try:body=page(route[3:] if route.startswith('/r/') else None).encode()
            except ValueError:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body);return
        parts=route.lstrip('/').split('/')
        if parts[0] in ('static','out','base'):
            folder=(ROOT/parts[0]).resolve();path=(ROOT/route.lstrip('/')).resolve()
            if path.is_relative_to(folder) and path.is_file() and path.suffix in ('.css','.js','.jpg','.png','.mp4','.json','.md'):
                return self.file_response(path)
        self.send_error(404)
    def do_HEAD(self):
        route=unquote(urlparse(self.path).path);path=(ROOT/route.lstrip('/')).resolve()
        if any(path.is_relative_to((ROOT/f).resolve()) for f in ('out','base','static')) and path.is_file() and path.suffix in ('.mp4','.png','.jpg','.css','.js'):
            return self.file_response(path)
        self.send_error(404)
    def do_POST(self):
        route=urlparse(self.path).path
        if route not in ('/api/make','/api/render'):return self.json_response({'error':'Not found'},404)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=16000:raise ValueError('Request too large or empty')
            payload={key:values[0] for key,values in parse_qs(self.rfile.read(length).decode()).items()}
            job_id=start_job('make' if route=='/api/make' else 'render',payload)
            self.json_response({'id':job_id},202)
        except ValueError as error:self.json_response({'error':str(error)},400)
    def log_message(self,*args):pass

if __name__=='__main__':
    print('Content studio: http://localhost:8000',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8000),H).serve_forever()
