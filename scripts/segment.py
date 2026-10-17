import numpy as np, json, sys
S=sys.argv[1]
d=np.load(S+"/feat.npz"); t,db,voi,vad=d['t'],d['db'],d['voi'],d['vad']
c=np.load(S+"/feat2.npz"); cen=c['cen']
N=len(t); dt=0.01
active=db>-47
runs=[];i=0
while i<N:
    if active[i]:
        j=i
        while j<N and active[j]: j+=1
        runs.append([i,j]); i=j
    else: i+=1
# merge across raw gaps <=0.10s (natural micro pauses stay)
m=[]
for r in runs:
    if m and (r[0]-m[-1][1])*dt<=0.10: m[-1][1]=r[1]
    else: m.append(list(r))
voiced=(voi>0.55)&(db>-42)
breathy=(voi<0.5)&(db<-33)&(cen<3000)
seg=[];log=[]
for a,b in m:
    if voiced[a:b].sum()<3:
        log.append(("sem voz (respiracao/ruido)",t[a],t[b-1])); continue
    # trim breathy head/tail longer than 0.1s
    h=a
    while h<b and breathy[h]: h+=1
    if (h-a)*dt>0.10: log.append(("inspiracao",t[a],t[h])); a=h-4
    e=b
    while e>a and breathy[e-1]: e-=1
    if (b-e)*dt>0.10: log.append(("expiracao",t[e],t[b-1])); b=e+4
    seg.append([t[a],t[b-1]])
# pads with clamp
out=[]
for k,(s,e) in enumerate(seg):
    ps=0.03 if k==0 else min(0.03,(s-seg[k-1][1])/2)
    pe=0.05 if k==len(seg)-1 else min(0.05,(seg[k+1][0]-e)/2)
    out.append([round(max(0,s-ps),3),round(e+pe,3)])
json.dump(out,open(S+"/keep.json","w"))
tot=sum(e-s for s,e in out)
print("segmentos",len(out),"duracao final",round(tot,2),"de",round(t[-1],2))
for l in log: print(" ",l[0],round(l[1],2),round(l[2],2))
gaps=[out[k+1][0]-out[k][1] for k in range(len(out)-1)]
print("maior gap restante",round(max(gaps),3))
