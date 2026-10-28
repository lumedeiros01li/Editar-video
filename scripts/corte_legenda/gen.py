import json,re
d=json.load(open("words_out.json")); W=d["words"]; SW=d["switch"]; TOTAL=d["total"]
LIME="&H70FEED&"   # BGR de #EDFE70
def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
head="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Leg,Inter Black,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,9,0,5,60,60,0,1
Style: HookS,Inter Black,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,6,2,5,40,40,0,1
Style: HookBig,Inter Black,128,&H00000000,&H00000000,&H70FEED,&H00000000,0,0,0,0,100,100,0,0,3,20,0,5,40,40,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
for k in range(1,len(W)):
    if W[k][1]<W[k-1][1]+0.08: W[k][1]=W[k-1][1]+0.08
ev=[]
# ---- gancho (só antes da troca de fundo) ----
pop=r"{\fad(120,140)\fscx70\fscy70\t(0,220,\fscx100\fscy100)}"
H0,H1=0.0,SW-0.02
ev.append(f"Dialogue: 1,{ts(H0)},{ts(H1)},HookS,,0,0,0,,{{\\pos(540,330)}}{pop}QUASE")
ev.append(f"Dialogue: 0,{ts(H0)},{ts(H1)},HookBig,,0,0,0,,{{\\pos(540,470)}}{{\\fad(120,140)\\fscx60\\fscy60\\t(0,260,\\fscx100\\fscy100)}}US$ 100.000")
ev.append(f"Dialogue: 1,{ts(H0)},{ts(H1)},HookS,,0,0,0,,{{\\pos(540,600)}}{pop}POR ANO PARA SEU FILHO")
ev.append(f"Dialogue: 1,{ts(H0)},{ts(H1)},HookS,,0,0,0,,{{\\pos(540,675)}}{pop}ESTUDAR NOS EUA")
# ---- legenda (o vídeo todo) ----
groups=[];cur=[]
for w in W:
    txt=w[0].rstrip(",.!?").upper()
    brk=w[0][-1] in ",.!?"
    L=sum(len(x[0].rstrip(',.!?')) for x in cur)+len(cur)+len(txt)
    if cur and (len(cur)>=3 or L>20): groups.append(cur);cur=[]
    cur.append((txt,w[1],w[2],w[0]))
    if brk: groups.append(cur);cur=[]
if cur:groups.append(cur)
for g in groups:
    for k,(t,s,e,raw) in enumerate(g):
        parts=[]
        for j,(tt,_,_,_) in enumerate(g):
            parts.append(("{\\c"+LIME+"}"+tt+"{\\c&HFFFFFF&}") if j==k else tt)
        end=e if k<len(g)-1 else min(e+0.12,TOTAL)
        nxt=next((w[1] for w in W if w[1]>s+1e-6),TOTAL)
        end=max(min(end,nxt),s+0.05)
        ev.append(f"Dialogue: 2,{ts(s)},{ts(end)},Leg,,0,0,0,,{{\\pos(540,1740)}}{' '.join(parts)}")
open("sub.ass","w").write(head+"\n".join(ev)+"\n")
print(len(groups),"grupos de legenda")
