import numpy as np, json, torch, sys
from silero_vad import load_silero_vad
S=sys.argv[1]
sr=16000
a=np.fromfile(S+"/a.raw",dtype=np.int16).astype(np.float32)/32768
hop=160; win=480
n=(len(a)-win)//hop
# energy
fr=np.lib.stride_tricks.sliding_window_view(a,win)[::hop][:n]
db=20*np.log10(np.sqrt((fr**2).mean(1))+1e-9)
# voicing via normalized autocorr (lag 2.5ms-12.5ms => 80-400Hz)
fr0=fr-fr.mean(1,keepdims=True)
F=np.fft.rfft(fr0,n=1024)
ac=np.fft.irfft(np.abs(F)**2)[:, :win]
ac=ac/(ac[:,:1]+1e-9)
lo,hi=int(sr/400),int(sr/75)
voi=ac[:,lo:hi].max(1)
# silero per-frame prob (32ms)
m=load_silero_vad(onnx=True); m.reset_states()
w=torch.from_numpy(a)
p=[float(m(w[i:i+512],sr)) for i in range(0,len(a)-512,512)]
p=np.array(p)
t=np.arange(n)*hop/sr+win/2/sr
vad=np.interp(t,np.arange(len(p))*512/sr+256/sr,p)
np.savez(S+"/feat.npz",t=t,db=db,voi=voi,vad=vad)
