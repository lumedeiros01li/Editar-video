import numpy as np, sys
S=sys.argv[1]
a=np.fromfile(S+"/a.raw",dtype=np.int16).astype(np.float32)/32768
hop,win=160,480
fr=np.lib.stride_tricks.sliding_window_view(a,win)[::hop]
d=np.load(S+"/feat.npz"); n=len(d['t']); fr=fr[:n]
P=np.abs(np.fft.rfft(fr*np.hanning(win),n=512))**2
f=np.fft.rfftfreq(512,1/16000)
cen=(P*f).sum(1)/(P.sum(1)+1e-12)
hf=P[:,f>3000].sum(1)/(P.sum(1)+1e-12)
np.savez(S+"/feat2.npz",cen=cen,hf=hf)
