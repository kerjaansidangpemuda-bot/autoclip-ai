import argparse, json, re, subprocess, sys, urllib.request
from pathlib import Path

OUT=Path('output')

def run(cmd): subprocess.run(cmd,check=True)
def duration(path):
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)],capture_output=True,text=True,check=True)
    return float(json.loads(r.stdout)['format']['duration'])

def acquire(url):
    if re.match(r'^https://(?:www\.|m\.)?(youtube\.com|youtu\.be|tiktok\.com)/',url,re.I):
        run(['yt-dlp','--no-playlist','--max-filesize','500M','-f','bv*+ba/b','--merge-output-format','mp4','-o','source.%(ext)s',url])
        paths=list(Path('.').glob('source.*'))
        if not paths: raise RuntimeError('Tidak berhasil mengambil video dari platform.')
        return paths[0]
    from urllib.parse import urlparse

host = (urlparse(response.url).hostname or "").lower()
allowed = (
    host == "github.com"
    or host.endswith(".github.com")
    or host == "githubusercontent.com"
    or host.endswith(".githubusercontent.com")
    or host == "githubassets.com"
    or host.endswith(".githubassets.com")
)

if not allowed or urlparse(response.url).scheme != "https":
    raise ValueError("Redirect lampiran tidak diizinkan.")
    req=urllib.request.Request(url,headers={'User-Agent':'AUTOCLIP-AI/1.1'})
    with urllib.request.urlopen(req,timeout=60) as response, open('source.mp4','wb') as f:
        if not response.url.startswith(('https://github.com/','https://github.githubassets.com/','https://objects.githubusercontent.com/')):
            raise ValueError('Redirect lampiran tidak diizinkan.')
        size=0
        while True:
            chunk=response.read(1024*1024)
            if not chunk:break
            size+=len(chunk)
            if size>500*1024*1024:raise ValueError('File melebihi 500 MB.')
            f.write(chunk)
    return Path('source.mp4')

def transcribe(src):
    from faster_whisper import WhisperModel
    model=WhisperModel('tiny',device='cpu',compute_type='int8')
    segs,_=model.transcribe(str(src),vad_filter=True,beam_size=1)
    return [{'start':s.start,'end':s.end,'text':s.text.strip()} for s in segs]

def windows(segs,d):
    if d<45:raise ValueError('Video minimal 45 detik agar 3 klip tidak tumpang tindih.')
    c=[]
    for s in segs:
        a=max(0,min(d-15,s['start']-1)); b=min(d,a+25)
        if b-a<15:continue
        covered=[x for x in segs if x['start']<b and x['end']>a]
        score=sum(len(x['text'].split()) for x in covered)
        c.append((score,a,b))
    c.sort(reverse=True)
    picked=[]
    for _,a,b in c:
        if all(b<=x or a>=y for x,y in picked):picked.append((a,b))
        if len(picked)==3:break
    for i in range(0,101):
        if len(picked)==3:break
        a=(d-15)*i/100;b=min(d,a+25)
        if b-a>=15 and all(b<=x or a>=y for x,y in picked):picked.append((a,b))
    if len(picked)!=3:raise ValueError('Tidak bisa memilih 3 segmen tanpa tumpang tindih.')
    return sorted(picked)

def srt(segs,a,b,path):
    def ts(v):
        n=round(max(0,v)*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000)
        return f'{h:02}:{m:02}:{s:02},{n:03}'
    lines=[]
    for seg in segs:
        x=max(a,seg['start']);y=min(b,seg['end'])
        if y-x<.15 or not seg['text']:continue
        lines.extend([str(len(lines)//4+1),f'{ts(x-a)} --> {ts(y-a)}',seg['text'],''])
    path.write_text('\n'.join(lines),encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);args=p.parse_args()
    OUT.mkdir(exist_ok=True)
    src=acquire(args.url)
    d=duration(src);segs=transcribe(src);spans=windows(segs,d)
    for i,(a,b) in enumerate(spans,1):
        srt(segs,a,b,OUT/f'clip_{i}.srt')
        vf='scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1'
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(a),'-i',str(src),'-t',str(b-a),'-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','27','-c:a','aac','-b:a','96k','-movflags','+faststart',str(OUT/f'clip_{i}.mp4')])
    print('Selesai: 3 MP4 + 3 subtitle SRT di output/')

if __name__=='__main__':
    try:main()
    except Exception as e:print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
