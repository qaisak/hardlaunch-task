"""Mood-matched footage with a face-safe reading panel and measured duration."""
from __future__ import annotations
import json
import math
import subprocess
import time
from pathlib import Path
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).parent
BASE_DIR = ROOT / 'base'
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
MOODS = ('deadpan', 'skeptical', 'thoughtful', 'disbelief', 'confused')

def _font(size):
    for p in (r'C:\Windows\Fonts\arialbd.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)

def read_time(text):
    return max(8.0, math.ceil((len(text.split()) / 2.6 + 2.5) * 10) / 10)

def infer_mood(text):
    rules = {'disbelief': ('argu', 'negotiat', 'madness', 'wrong', 'psychopath', 'unwell'),
             'skeptical': ('swears', 'judg', 'pretend', 'refus', 'apparently', 'trust'),
             'thoughtful': ('meditat', 'sleep', 'breathe', 'calm', 'mind', 'quiet', 'stress'),
             'confused': ('lost', 'confus', 'nothing works', 'photocopy', 'grammar', 'trying to learn')}
    scores = {m: sum(text.lower().count(w) for w in words) for m, words in rules.items()}
    mood = max(scores, key=scores.get)
    return mood if scores[mood] else 'deadpan'

def catalogue():
    p = BASE_DIR / 'clips.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

def pick_base(text='', reaction=None, clip_name=None):
    entries = catalogue()
    clips = sorted(p for p in BASE_DIR.glob('*') if p.suffix.lower() in ('.mp4', '.mov', '.m4v', '.webm'))
    if clip_name:
        selected = next((p for p in clips if p.name == clip_name and p.name in entries), None)
        if selected is None:
            raise ValueError('Choose a clip from the reaction library')
        return selected
    mood = reaction if reaction in MOODS else infer_mood(text)
    matches = [p for p in clips if entries.get(p.name, {}).get('mood') == mood or mood in entries.get(p.name, {}).get('tags', [])]
    matches.sort(key=lambda p: -entries.get(p.name, {}).get('priority', 0))
    return matches[0] if matches else (clips[0] if clips else None)

def text_layer(text, path, brand=''):
    img = Image.new('RGBA', (W,H), (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.rectangle((0,1050,W,H), fill=(19,19,23,255))
    for size in range(54,35,-2):
        font = _font(size)
        lines, line = [], ''
        for word in text.split():
            candidate = (line+' '+word).strip()
            if d.textlength(candidate,font=font)>860:
                if not line or d.textlength(word,font=font)>860:
                    raise ValueError('Unbroken word too wide for video')
                lines.append(line)
                line=word
            else:
                line=candidate
        if line:
            lines.append(line)
        line_h=size+14
        if len(lines)*line_h<=630:
            break
    else:
        raise ValueError('Shorten overlay: too long to render readably')
    y=1110+(630-len(lines)*line_h)//2
    for line in lines:
        d.text((90,y),line,font=font,fill='white',anchor='lt')
        y+=line_h
    label=brand
    while label and d.textlength(label,font=_font(30))>860:
        label=label[:-1]
    d.text((90,1770),label,font=_font(30),fill=(185,185,195),anchor='lt')
    img.save(path)
    return path

def render_mp4(text, out, brand='', still=None, reaction=None, clip_name=None):
    out.parent.mkdir(parents=True,exist_ok=True)
    layer=text_layer(text,out.with_suffix('.overlay.png'),brand)
    duration=read_time(text)
    base=pick_base(text,reaction,clip_name)
    info=catalogue().get(base.name,{}) if base else {}
    if base:
        if info.get('fit') == 'contain':
            filters=("[0:v]split=2[a][b];[a]scale=1080:1050:force_original_aspect_ratio=increase,"
                     "crop=1080:1050,boxblur=25:2[blur];[b]scale=1080:1050:force_original_aspect_ratio=decrease[fg];"
                     "[blur][fg]overlay=(W-w)/2:(H-h)/2,pad=1080:1920:0:0:color=black,setsar=1[bg];"
                     "[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]")
        else:
            filters=(f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                 f"crop=1080:1050:0:{info.get('crop_y',300)},pad=1080:1920:0:0:color=black,setsar=1[bg];"
                 '[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]')
        inputs=['-stream_loop','-1','-i',str(base),'-i',str(layer)]
        how=f"{info.get('name', base.name)} · {duration:.1f}s · silent"
    else:
        bg=out.with_suffix('.placeholder.png')
        image=Image.new('RGB',(W,H),(30,30,35))
        ImageDraw.Draw(image).text((90,450),'Preview: add footage to base/',font=_font(42),fill='white')
        image.save(bg)
        inputs=['-loop','1','-i',str(bg),'-i',str(layer)]
        filters='[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]'
        how=f'PLACEHOLDER: no base footage; {duration:.1f}s; silent'
    pending=out.with_name(out.stem+'.rendering.mp4')
    cmd=[FFMPEG,'-y',*inputs,'-filter_complex',filters,'-map','[v]','-t',str(duration),'-r','30',
         '-c:v','libx264','-preset','veryfast','-crf','20','-an','-movflags','+faststart',str(pending)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError('Video render failed: '+result.stderr[-1500:])
    # Windows scanners or an active preview can briefly hold the previous export.
    for attempt in range(20):
        try:
            pending.replace(out)
            break
        except PermissionError:
            if attempt == 19:
                raise RuntimeError('The previous video is still open in another program. Close it and rebuild; the new render is saved as ' + pending.name)
            time.sleep(0.25)
    poster = out.with_name('post.png')
    subprocess.run([FFMPEG, '-v', 'error', '-y', '-ss', '0.4', '-i', str(out), '-frames:v', '1', str(poster)], check=True)
    out.with_suffix('.video.json').write_text(json.dumps({'clip':base.name if base else None,
        'reaction':info.get('mood'),'name':info.get('name'), 'source':info.get('source'),
        'selection':'manual' if clip_name else ('model' if reaction in MOODS else 'text-rule fallback'),
        'duration_s':duration,'word_count':len(text.split()),'audio':'silent','description':how},indent=2),encoding='utf-8')
    return out,how
