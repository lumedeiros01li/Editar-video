import numpy as np, cv2, os, json, sys
S=sys.argv[1]
fs=sorted(os.listdir(S+"/masks")); pts=[]
for f in fs:
    m=cv2.imread(S+"/masks/"+f,0)>128
    rows=np.where(m.any(1))[0]
    if len(rows)==0: pts.append(pts[-1] if pts else [0.3,0.4]); continue
    top=rows[0]; band=m[top:top+int(0.45*720)]
    ys,xs=np.nonzero(band)
    pts.append([xs.mean()/1280,(top+0.25*720)/720])
p=np.array(pts)
k=np.ones(15)/15
sm=np.stack([np.convolve(np.pad(p[:,i],7,mode='edge'),k,'valid') for i in range(2)],1)
tl=json.load(open(S+"/timeline.json"))
trans=[s['t'] for s in tl['segments'] if s['gap']>=0.43 and s['t']>0]
json.dump({"duration":tl['duration'],"segments":tl['segments'],"transitions":trans,"head":sm.round(4).tolist()},open(S+"/scene_data.json","w"))
print(len(sm),sm.min(0),sm.max(0),trans)
