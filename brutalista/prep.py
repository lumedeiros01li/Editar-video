# Pre-processing: paper texture, halftone photos/cutouts, footage frames
import cv2, numpy as np, os, sys, glob
CUT, FOOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT+"/img", exist_ok=True)
INK = np.array([20,20,22],np.float32)/255     # BGR
PAPER = np.array([226,236,242],np.float32)/255  # warm off-white (BGR)
rng = np.random.default_rng(7)

def paper(w=1080,h=1920):
    base = np.ones((h,w,3),np.float32)*np.array([214,228,236],np.float32)/255
    low = cv2.resize(rng.random((24,14)).astype(np.float32),(w,h),interpolation=cv2.INTER_CUBIC)
    fib = cv2.GaussianBlur(rng.random((h,w)).astype(np.float32),(0,0),0.8)
    streak = cv2.blur(rng.random((h,w)).astype(np.float32),(1,41))
    v = 1+0.05*(low-0.5)+0.06*(fib-0.5)+0.05*(streak-0.5)
    yy,xx = np.mgrid[0:h,0:w]; vig = 1-0.10*(((xx-w/2)/(w/2))**2+((yy-h/2)/(h/2))**2)
    img = base*(v*vig)[...,None]
    cv2.imwrite(OUT+"/img/paper.jpg",np.clip(img*255,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,92])

def halftone_gray(g, cell=7, ang=45):
    """g: 0..1 gray (1=white). returns 0..1 with round dots on a rotated grid"""
    h,w = g.shape
    yy,xx = np.mgrid[0:h,0:w].astype(np.float32)
    a = np.deg2rad(ang); u = xx*np.cos(a)+yy*np.sin(a); v = -xx*np.sin(a)+yy*np.cos(a)
    du = (u % cell)-cell/2; dv = (v % cell)-cell/2
    d = np.sqrt(du*du+dv*dv)
    dark = 1-cv2.GaussianBlur(g,(0,0),cell*0.45)
    r = cell*0.62*np.sqrt(np.clip(dark,0,1))
    return np.clip((d-r)+0.5,0,1)  # 1 paper, 0 ink, antialiased

def treat(bgr, contrast=1.35, mix=0.5, cell=7):
    g = cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
    g = cv2.createCLAHE(2.0,(8,8)).apply((g*255).astype(np.uint8)).astype(np.float32)/255
    g = np.clip((g-0.5)*contrast+0.52,0,1)
    ht = halftone_gray(g,cell)
    t = mix*g+(1-mix)*ht
    t = np.clip(t,0,1)[...,None]
    return INK*(1-t)+PAPER*t

def save_rgb(name, img, q=90):
    cv2.imwrite(f"{OUT}/img/{name}.jpg",np.clip(img*255,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,q])

def cutout(name, border=14, scale=1.0, **kw):
    im = cv2.imread(f"{CUT}/{name}.png",cv2.IMREAD_UNCHANGED)
    if scale!=1: im = cv2.resize(im,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
    pad = border+6
    im = cv2.copyMakeBorder(im,pad,pad,pad,pad,cv2.BORDER_CONSTANT,value=(0,0,0,0))
    rgb, a = im[...,:3], im[...,3].astype(np.float32)/255
    t = treat(rgb,**kw)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*border+1,2*border+1))
    ab = cv2.dilate((a>0.5).astype(np.uint8),k).astype(np.float32)
    ab = cv2.GaussianBlur(ab,(3,3),0)
    out = np.ones_like(t)*np.array([250,252,253],np.float32)/255
    out = out*(1-a[...,None])+t*a[...,None]
    rgba = np.dstack([np.clip(out*255,0,255).astype(np.uint8),(ab*255).astype(np.uint8)])
    cv2.imwrite(f"{OUT}/img/{name}.png",rgba)

paper()
for n,s in [("lula",1.25),("flavio",1.25),("scales",1.3),("news",1.3),("globe",1.3),("dollars",1.2),("bull",1.2),("coffee",1.1)]:
    cutout(n,scale=s)
lu = cv2.imread(f"{CUT}/lucas.jpg"); lu = cv2.resize(lu,None,fx=1.5,fy=1.5,interpolation=cv2.INTER_CUBIC)
save_rgb("lucas",treat(lu,mix=0.6,cell=6))
for n in ["congresso_lilas","congresso_azul","stf","nyse"]:
    im = cv2.imread(f"{CUT}/{n}.jpg"); im = cv2.resize(im,None,fx=1.2,fy=1.2,interpolation=cv2.INTER_CUBIC)
    save_rgb(n,treat(im,cell=8))
# trechos limpos do vídeo original (sem legenda antiga): quadro inicial, final, altura do recorte
CLIPS = {"chart": (24, 114, 920), "nyse": (24, 123, 780)}
for clip,(a,b,hcrop) in CLIPS.items():
    os.makedirs(f"{OUT}/foot/{clip}",exist_ok=True)
    for k,f in enumerate(sorted(glob.glob(f"{FOOT}/{clip}/*.jpg"))[a:b+1]):
        im = cv2.imread(f)[:hcrop]; im = cv2.resize(im,None,fx=1.2,fy=1.2,interpolation=cv2.INTER_CUBIC)
        save_rgb(f"../foot/{clip}/{k+1:04d}", treat(im,cell=8,contrast=1.5), q=85)
print("ok")
