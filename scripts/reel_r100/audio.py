import numpy as np, wave
SR=48000; DUR=32.5; N=int(SR*DUR)
L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(7)
def add(sig,t,gain=1.0,pan=0.0):
    i=int(t*SR); n=min(len(sig),N-i)
    if n<=0: return
    L[i:i+n]+=sig[:n]*gain*(1-max(pan,0)); R[i:i+n]+=sig[:n]*gain*(1+min(pan,0))
def env(n,a=0.003,d=0.2):
    t=np.arange(n)/SR; e=np.exp(-t/d); k=int(a*SR); e[:k]*=np.linspace(0,1,k); return e
def kick(g=1.0,big=False):
    dur=1.2 if big else 0.4; n=int(dur*SR); t=np.arange(n)/SR
    f=45+(120 if big else 90)*np.exp(-t*(18 if big else 30)); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*env(n,0.001,0.5 if big else 0.13)*g
def noise(dur,d,hp=True):
    n=int(dur*SR); x=rng.standard_normal(n)
    if hp: x=np.diff(np.concatenate([[0],x]))
    return x*env(n,0.001,d)
def tone(f,dur,d,harm=(1,0.4,0.15)):
    n=int(dur*SR); t=np.arange(n)/SR
    s=sum(a*np.sin(2*np.pi*f*(k+1)*t) for k,a in enumerate(harm)); return s*env(n,0.002,d)
def lowpass(x,a):
    y=np.zeros_like(x); p=0.0
    for i in range(len(x)): p+=a*(x[i]-p); y[i]=p
    return y
def saw(f,dur,d):
    n=int(dur*SR); t=np.arange(n)/SR; x=2*((t*f)%1)-1
    x=lowpass(x,0.08); return x*env(n,0.005,d)
def whoosh(dur=0.35,up=True):
    n=int(dur*SR); x=rng.standard_normal(n); t=np.linspace(0,1,n)
    a=(0.02+0.25*t) if up else (0.27-0.25*t)
    y=np.zeros(n); p=0.0
    for i in range(n): p+=a[i]*(x[i]-p); y[i]=p
    e=np.sin(np.pi*t)**2; return y*e*1.6
def riser(dur):
    n=int(dur*SR); t=np.arange(n)/SR; f=200*np.exp(t/dur*np.log(10))
    s=np.sin(2*np.pi*np.cumsum(f)/SR)*0.25+whoosh(dur)[:n]*0.8
    return s*(t/dur)**2

# --- timeline espelhada do HTML ---
def ease(p,mode=None):
    p=min(max(p,0),1); sm=p*p*(3-2*p)
    return 1-(1-p)**3 if mode=='out' else 0.7*p+0.3*sm
def seg(t,segs):
    x=segs[0][2]
    for s in segs:
        t0,t1,x0,x1=s[:4]; mode=s[4] if len(s)>4 else None
        if t<t0: return x
        x=x0+(x1-x0)*ease((t-t0)/(t1-t0),mode)
        if t<=t1: return x
    return x
XMAX=25.75
P1=[(2,5,0,8),(6,8,8,15),(9,11.5,15,XMAX)]
P2=[(20,22,0,8),(22,23.5,8,10),(23.5,24.7,10,15,'out'),(25,27,15,XMAX)]
def ticks(segs,t0,t1):
    out=[]; prev=0
    for t in np.arange(t0,t1,1/SR*20):
        x=seg(t,segs); k=int(np.floor(x+1e-6))
        if k>prev: out.append((t,k)); prev=k
    return out

beat=0.5
chords=[110.0, 87.31, 130.81, 98.0]  # A F C G (baixo)
def bassline(t0,t1,gain):
    for bt in np.arange(t0,t1-1e-6,beat):
        f=chords[int(bt/2)%4]
        add(saw(f,0.45,0.18),bt,gain)
def drums(t0,t1,step=beat,hats=True,kg=0.9):
    for bt in np.arange(t0,t1-1e-6,step):
        add(kick(kg),bt)
        if hats:
            add(noise(0.06,0.015),bt+beat/2,0.10,0.3)
    if hats:
        for bt in np.arange(t0+beat,t1-1e-6,2*beat): add(noise(0.18,0.06),bt,0.22,-0.2)  # clap leve

# pad contínuo
def pad(t0,t1,freqs,gain):
    n=int((t1-t0)*SR); t=np.arange(n)/SR
    s=sum(np.sin(2*np.pi*f*t+0.3*np.sin(2*np.pi*0.2*t)) for f in freqs)/len(freqs)
    e=np.minimum(1,np.minimum(t/0.4,(t1-t0-t)/0.4)); add(s*e,t0,gain)

# PARTE 1
add(kick(0.8),0.0); add(kick(0.6),1.0); add(riser(1.0),1.0,0.5)
pad(0,16.5,[220,261.6,329.6],0.05)
drums(2,11.5); bassline(2,11.5,0.35)
for t,k in ticks(P1,2,11.6): add(tone(1400+k*35,0.08,0.03),t,0.12,0.2)
for tf in [5.0,8.0,11.022]:
    add(whoosh(0.3),tf-0.25,0.6); add(noise(0.25,0.05),tf,0.35); add(kick(0.7),tf)
add(kick(0.9),11.5); add(noise(0.4,0.1,False),11.5,0.15)
drums(12.5,15.5,step=1.0,hats=False,kg=0.7)
for i,tr in enumerate([12.5,13.1,13.7,14.3,14.9]):
    f=523.25*2**(i*2/12); add(tone(f,0.6,0.25),tr,0.30 if i<4 else 0.45); add(tone(f*1.5,0.6,0.2),tr,0.12)
add(riser(1.0),15.5,0.9)
# VIRADA: batida forte
add(kick(1.4,big=True),16.5); add(noise(1.6,0.6,False),16.5,0.35); add(noise(0.6,0.15),16.5,0.5)
for f in [55,110,164.8]: add(saw(f,2.0,0.9),16.5,0.35)
pad(16.5,18.5,[174.6,220,261.6],0.07)
add(kick(0.9),17.5); add(riser(0.5),18.0,0.7)
# PARTE 2
add(kick(1.1),18.5); add(noise(0.5,0.12),18.5,0.35); add(whoosh(0.35,False),18.5,0.5)
pad(18.5,32.5,[220,261.6,329.6],0.05)
add(kick(0.6),19.5); add(riser(0.5),19.5,0.5)
drums(20,27); bassline(20,27,0.35)
for t,k in ticks(P2,20,27.1): add(tone(1400+k*35,0.08,0.03),t,0.12,0.2)
for tf in [20.554,24.4,26.822]:
    add(whoosh(0.3),tf-0.25,0.6); add(noise(0.25,0.05),tf,0.35); add(kick(0.7),tf)
add(tone(880,0.3,0.1),23.502,0.2)
add(kick(0.9),27.0); add(noise(0.4,0.1,False),27.0,0.15)
drums(28,30.5,step=1.0,hats=False,kg=0.7)
for i,tr in enumerate([28.0,28.5,29.0,29.5,30.0]):
    f=523.25*2**(i*2/12); add(tone(f,0.5,0.22),tr,0.30 if i<4 else 0.45); add(tone(f*1.5,0.5,0.18),tr,0.12)
add(kick(1.1,big=True),30.5); add(noise(1.2,0.5,False),30.5,0.2)
for f in [110,220,261.6,329.6]: add(tone(f,2.0,0.9,(1,0.3)),30.5,0.12)

mix=np.stack([L,R],1)
mix=np.tanh(mix*1.3)/np.tanh(1.3)
mix/=np.abs(mix).max()/0.62
fo=int(0.3*SR); mix[-fo:]*=np.linspace(1,0,fo)[:,None]
with wave.open('audio.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
print('ok')
