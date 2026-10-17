import argparse, json, os, re, subprocess, sys
from pathlib import Path


def run(args):
    subprocess.run(args, check=True)

def probe(path):
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)],capture_output=True,text=True,check=True)
    return float(json.loads(r.stdout)['format']['duration'])

def download(url, directory):
    if not re.match(r'^https://(?:www\.|m\.)?(youtube\.com|youtu\.be|tiktok\.com)/',url,re.I):
        raise ValueError('Hanya link YouTube/TikTok HTTPS yang didukung.')
    run(['yt-dlp','--no-playlist','--max-filesize','500M','-f','bv*+ba/b','--merge-output-format','mp4','-o',str(directory/'source.%(ext)s'),url])
    files=list(directory.glob('source.*'))
    if not files: raise RuntimeError('Gagal mengunduh video.')
    return files[0]

def speech_segments(source):
    from faster_whisper import WhisperModel
    model=WhisperModel('tiny',device='cpu',compute_type='int8')
    segments,_=model.transcribe(str(source),vad_filter=True,beam_size=1)
    return [{'start':s.start,'end':s.end,'text':s.text.strip()} for s in segments]

def choose_windows(segments,duration):
    # Prefer speech-dense spans with clean boundaries, and avoid overlap.
    candidates=[]
    for s in segments:
        start=max(0.,s['start']-1)
        end=min(duration,start+25.)
        if end-start<15: start=max(0.,end-15.)
        if end-start<15: continue
        covered=[x for x in segments if x['start']<end and x['end']>start]
        words=sum(len(x['text'].split()) for x in covered)
        score=words + 2*sum(any(p in x['text'] for p in '?!') for x in covered)
        candidates.append((score,start,end))
    candidates.sort(reverse=True)
    chosen=[]
    for _,start,end in candidates:
        if all(min(end,b)-max(start,a)<=0 for a,b in chosen): chosen.append((start,end))
        if len(chosen)==3: break
    # Fallback when transcript is sparse or missing
    for ratio in (0.05,0.4,0.75,0.2,0.6):
        if len(chosen)==3: break
        start=min(max(0,duration-15),duration*ratio)
        end=min(duration,start+25)
        if end-start>=15 and all(min(end,b)-max(start,a)<=0 for a,b in chosen): chosen.append((start,end))
    if len(chosen)<3: raise ValueError('Video terlalu pendek untuk membuat 3 klip yang tidak tumpang tindih (minimal sekitar 45 detik).')
    return sorted(chosen)

def subtitles(segments,start,end,path):
    def stamp(t):
        ms=max(0,round(t*1000));h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    lines=[];idx=1
    for seg in segments:
        a=max(start,seg['start']);b=min(end,seg['end'])
        if b-a<.15 or not seg['text']: continue
        lines.extend([str(idx),f'{stamp(a-start)} --> {stamp(b-start)}',seg['text'],'']);idx+=1
    path.write_text('\n'.join(lines),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--url',required=True);args=ap.parse_args()
    out=Path('output');out.mkdir(exist_ok=True)
    src=download(args.url,Path('.'))
    duration=probe(src)
    segments=speech_segments(src)
    windows=choose_windows(segments,duration)
    for i,(start,end) in enumerate(windows,1):
        srt=out/f'clip_{i}.srt';subtitles(segments,start,end,srt)
        # Center crop for stable 9:16 output; automatic face tracking is not implemented.
        vf='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1'
        run(['ffmpeg','-y','-ss',str(start),'-i',str(src),'-t',str(end-start),'-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','25','-c:a','aac','-b:a','128k','-movflags','+faststart',str(out/f'clip_{i}.mp4')])
    print('Berhasil membuat 3 MP4 dan subtitle SRT terpisah di output/')

if __name__=='__main__':
    try:main()
    except Exception as e:print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
