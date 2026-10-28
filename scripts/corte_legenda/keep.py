import numpy as np, json
a=np.fromfile("a.raw",dtype=np.int16).astype(np.float32)/32768
hop,win=160,480
n=(len(a)-win)//hop
fr=np.lib.stride_tricks.sliding_window_view(a,win)[::hop][:n]
db=20*np.log10(np.sqrt((fr**2).mean(1))+1e-9)
act=db>-45
runs=[];i=0
while i<n:
    if act[i]:
        j=i
        while j<n and act[j]:j+=1
        runs.append([i*.01,j*.01]);i=j
    else:i+=1
m=[]
for r in runs:
    if m and r[0]-m[-1][1]<=0.10:m[-1][1]=r[1]
    else:m.append(r)
# ruído, respiração e hesitação (conferido por voicing + transcrição)
DROP=[(26.9,27.0),(45.3,45.6)]
m=[r for r in m if not any(abs(r[0]-d[0])<0.1 and abs(r[1]-d[1])<0.1 for d in DROP)]
PS,PE=0.05,0.05
keep=[]
for s,e in m:
    s,e=max(0,s-PS),min(55.66,e+PE)
    if keep and s-keep[-1][1]<=0.10: keep[-1][1]=e
    else: keep.append([s,e])
keep=[[round(s,3),round(e,3)] for s,e in keep]
json.dump(keep,open("keep.json","w"))
tot=sum(e-s for s,e in keep)
print(len(keep),"segmentos",round(tot,2),"s")
t=0
for s,e in keep: print(f"{s:6.2f}-{e:6.2f} -> out {t:6.2f}"); t+=e-s
