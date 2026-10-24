import json,numpy as np,wave,torch
from silero_vad import load_silero_vad,get_speech_timestamps
W=__import__('sys').argv[1]
vad=load_silero_vad(onnx=True)
CUTS={"v1":[(22.9,24.84),(26.16,26.62)],"v2":[(12.9,19.46)]}
FIX={"computador,":"contador,","pólice.":"apólice."}
out=[];words=[];T=0.0
for v in ["v1","v2"]:
    w=wave.open(f"{W}/{v}.wav"); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    dur=len(a)/16000
    ts=get_speech_timestamps(torch.from_numpy(a),vad,sampling_rate=16000,min_silence_duration_ms=110,min_speech_duration_ms=120,speech_pad_ms=0,threshold=0.45,return_seconds=True)
    segs=[[t['start'],t['end']] for t in ts]
    # subtract manual cuts
    for cs,ce in CUTS[v]:
        ns=[]
        for s,e in segs:
            if e<=cs or s>=ce: ns.append([s,e]); continue
            if s<cs: ns.append([s,cs])
            if e>ce: ns.append([ce,e])
        segs=ns
    segs=[s for s in segs if s[1]-s[0]>0.12]
    # pads
    pad=[]
    for k,(s,e) in enumerate(segs):
        gp=s-segs[k-1][1] if k else 1; gn=segs[k+1][0]-e if k+1<len(segs) else 1
        incut=lambda x:any(cs<=x<=ce for cs,ce in CUTS[v])
        ps=min(0.06,gp/2); pe=min(0.09,gn/2)
        if incut(s-0.01): ps=0.0
        if incut(e+0.01): pe=0.0
        pad.append([max(0,s-ps),min(dur,e+pe)])
    # merge tiny gaps (<0.10s) -> keep natural
    m=[]
    for s,e in pad:
        if m and s-m[-1][1]<0.10 and not any(m[-1][1]<=cs+0.02 and s>=ce-0.02 for cs,ce in CUTS[v]): m[-1][1]=e
        else: m.append([s,e])
    ws=json.load(open(f"{W}/{v}_words.json"))
    for s,e in m:
        out.append({"src":v,"s":round(s,3),"e":round(e,3),"t":round(T,3)})
        for x in ws:
            o=x["s"]+0.12
            if s-0.28<=o<e-0.05:
                words.append({"w":FIX.get(x["w"],x["w"]),"t":round(T+max(0,o-s),3),"src":v})
        T+=e-s
# word ends = next word start (capped)
for i,x in enumerate(words):
    nx=words[i+1]["t"] if i+1<len(words) else x["t"]+0.5
    x["e"]=round(min(nx,x["t"]+0.9),3)
json.dump({"segments":out,"words":words,"duration":round(T,3)},open(f"{W}/timeline.json","w"),ensure_ascii=False,indent=1)
for k,s in enumerate(out): print(k,s, " ".join(x["w"] for x in words if s["t"]<=x["t"]<s["t"]+s["e"]-s["s"]-0.001))
print("dur",round(T,2))
