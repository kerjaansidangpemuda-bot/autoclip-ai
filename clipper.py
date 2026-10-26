import argparse, json, math, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlparse

OUT = Path('output')

def run(cmd):
    subprocess.run(cmd, check=True)

def get_duration(src):
    p = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(src)],capture_output=True,text=True,check=True)
    return float(json.loads(p.stdout)['format']['duration'])

def validate_url(url):
    p=urlparse(url)
    host=(p.hostname or '').lower()
    allowed={'youtube.com','www.youtube.com','m.youtube.com','youtu.be','www.youtu.be','tiktok.com','www.tiktok.com','m.tiktok.com','vm.tiktok.com','vt.tiktok.com'}
    if p.scheme!='https' or host not in allowed or p.username or p.password or p.port:
        raise ValueError('Hanya URL HTTPS YouTube atau TikTok yang didukung.')
    return url

def acquire(url):
    validate_url(url)
    run(['yt-dlp','--no-playlist','--max-filesize','500M','--socket-timeout','30','--retries','2','-f','bv*+ba/b','--merge-output-format','mp4','-o','source.%(ext)s',url])
    files=[p for p in Path('.').glob('source.*') if p.suffix.lower() in ('.mp4','.mkv','.webm')]
    if not files: raise RuntimeError('Video tidak berhasil diambil. Platform mungkin membatasi akses otomatis.')
    return files[0]

def transcribe(src):
    from faster_whisper import WhisperModel
    model=WhisperModel('tiny',device='cpu',compute_type='int8')
    segments,_=model.transcribe(str(src),vad_filter=True,beam_size=1)
    return [{'start':s.start,'end':s.end,'text':s.text.strip()} for s in segments]

def choose_segments(segs,d):
    if d<45: raise ValueError('Video minimal 45 detik.')
    length=min(25.0,d/3)
    # Score candidate windows by spoken word density, not semantic virality.
    candidates=[]
    for i in range(max(1,int((d-length)/2)+1)):
        start=min(i*2,d-length)
        end=start+length
        score=sum(len(s['text'].split())*max(0,min(end,s['end'])-max(start,s['start']))/max(.1,s['end']-s['start']) for s in segs)
        candidates.append((score,start,end))
    candidates.sort(reverse=True)
    chosen=[]
    for _,a,b in candidates:
        if all(b<=x or a>=y for x,y in chosen):chosen.append((a,b))
        if len(chosen)==3:break
    if len(chosen)<3:
        chosen=[(i*length,(i+1)*length) for i in range(3)]
    return sorted(chosen)

def timestamp(t):
    n=round(max(0,t)*1000)
    h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def write_srt(segs,a,b,path):
    lines=[]
    for seg in segs:
        x=max(a,seg['start']);y=min(b,seg['end'])
        if y-x<.15 or not seg['text']:continue
        lines += [str(len(lines)//4+1),f'{timestamp(x-a)} --> {timestamp(y-a)}',seg['text'],'']
    path.write_text('\n'.join(lines),encoding='utf-8')
    return bool(lines)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',required=True);args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    print('Mengambil video...',flush=True)
    src=acquire(args.url)
    d=get_duration(src)
    print(f'Durasi: {d:.1f}s. Transkripsi...',flush=True)
    segs=transcribe(src)
    for i,(a,b) in enumerate(choose_segments(segs,d),1):
        srt=OUT/f'clip_{i}.srt'
        has_sub=write_srt(segs,a,b,srt)
        vf='scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1'
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(a),'-i',str(src),'-t',str(b-a),'-vf',vf]
        # Subtitles are provided as SRT, not burned in: avoids font/libass assumptions.
        cmd+=['-c:v','libx264','-preset','veryfast','-crf','27','-c:a','aac','-b:a','96k','-movflags','+faststart',str(OUT/f'clip_{i}.mp4')]
        print(f'Membuat klip {i}/3 ({a:.1f}-{b:.1f}s)...',flush=True)
        run(cmd)
    print('Selesai: 3 MP4 dan 3 SRT di output/',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print(f'ERROR: {e}',file=sys.stderr)
        sys.exit(1)
