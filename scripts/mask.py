import numpy as np, sys, os, cv2
from ai_edge_litert.interpreter import Interpreter
S=sys.argv[1]; only=sys.argv[2:] 
it=Interpreter(model_path=S+"/seg/node_modules/@mediapipe/selfie_segmentation/selfie_segmentation_landscape.tflite",num_threads=4)
it.allocate_tensors()
iin=it.get_input_details()[0]['index']; iout=it.get_output_details()[0]['index']
def guided(I,p,r,eps):
    bf=lambda x: cv2.boxFilter(x,-1,(2*r+1,2*r+1))
    mI=bf(I); mp=bf(p); cIp=bf(I*p)-mI*mp; vI=bf(I*I)-mI*mI
    a=cIp/(vI+eps); b=mp-a*mI
    return bf(a)*I+bf(b)
files=sorted(os.listdir(S+"/frames_in"))
if only: files=[f for f in files if f in only]
prev=None
for f in files:
    img=cv2.imread(S+"/frames_in/"+f)
    rgb=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    x=cv2.resize(rgb,(256,144),interpolation=cv2.INTER_AREA).astype(np.float32)/255.
    it.set_tensor(iin,x[None]); it.invoke()
    m=it.get_tensor(iout)[0,:,:,0]
    if m.min()<0 or m.max()>1: m=1/(1+np.exp(-m))
    m=cv2.resize(m,(1280,720),interpolation=cv2.INTER_CUBIC)
    # temporal smoothing
    if prev is not None: m=0.6*m+0.4*prev
    prev=m
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)/255.
    r=guided(g,m.astype(np.float32),8,1e-3)
    r=np.clip((r-0.45)/0.25,0,1)
    cv2.imwrite(S+"/masks/"+f.replace(".jpg",".png"),(r*255).astype(np.uint8))
