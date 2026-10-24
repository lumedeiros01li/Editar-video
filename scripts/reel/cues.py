import json,sys
W=sys.argv[1]
d=json.load(open(W+"/timeline.json"))
segs=d["segments"]; words=d["words"]
# extend last segment to natural end of clip (CTA hold)
segs[-1]["e"]=34.80
dur=round(segs[-1]["t"]+segs[-1]["e"]-segs[-1]["s"],3)
w=lambda i: words[i]["t"]
E=[];SFX=[]
Y=330; LY=545
def emoji(code,x,y,size,tin,tout,anim="pop",sfx="pop",pitch=1.0,**kw):
    E.append(dict(type="emoji",code=code,x=x,y=y,size=round(size*1.15),tin=round(tin,3),tout=round(tout,3),anim=anim,**kw))
    if sfx: SFX.append(dict(kind=sfx,t=round(tin,3),pitch=pitch))
def label(text,x,y,tin,tout,color="#7B2FF7",**kw):
    E.append(dict(type="label",text=text,x=x,y=y,tin=round(tin,3),tout=round(tout,3),color=color,**kw))
def fx(kind,tin,tout,**kw): E.append(dict(type=kind,tin=round(tin,3),tout=round(tout,3),**kw))
def sfx(kind,t,pitch=1.0,gain=1.0): SFX.append(dict(kind=kind,t=round(t,3),pitch=pitch,gain=gain))

# 1 hook: casa + agua
emoji("1f3e0",370,Y,300,0.05,2.5,pitch=1.0)
emoji("1f4a7",720,Y-20,230,w(7)-0.05,2.5,anim="drop",pitch=1.25)
label("Registro de água?",540,LY,w(5),2.5)
# 2 familia sabe?
emoji("1f468-200d-1f469-200d-1f467",540,Y,320,w(13)-0.05,4.5)
emoji("2753",800,Y-110,150,w(17)-0.05,4.5,anim="wobble",pitch=1.3)
label("Quem mora com você sabe?",540,LY,w(14),4.5)
# 3 dinheiro = agua
emoji("1f6b0",270,Y,240,4.6,5.68)
emoji("1f4b0",810,Y,260,w(19),5.68,pitch=1.2)
fx("bigtext",w(20)-0.05,5.68,text="=",x=540,y=Y,size=170)
sfx("pop",w(20)-0.05,1.5,0.7)
# 4 investido / qual banco
emoji("1f4c8",540,Y,290,w(26),8.0,anim="rise")
label("Sabe quanto tem investido",540,LY,w(27),8.0)
emoji("1f3e6",540,Y,300,w(29)+0.05,10.92)
for k,(x,y) in enumerate([(300,Y-90),(790,Y-120),(820,Y+80)]):
    emoji("2753",x,y,120,w(36)+k*0.12,10.92,anim="wobble",sfx="pop",pitch=1.3+k*0.1)
label("Mas ninguém sabe em qual banco",540,LY,w(30),10.92)
# 5 seguro / apolice
emoji("1f6e1-fe0f",540,Y,290,w(40),13.78,moveTo=[300,Y,w(43),0.35,230])
emoji("1f648",780,Y,250,w(46),13.78,pitch=1.15)
label("Seguro de vida",540,LY,w(40),w(43))
label("Nunca viu a apólice",540,LY,w(47),13.78)
# 6 contador advogado assessor
for k,(c,lab,i) in enumerate([("1f9ee","Contador",51),("2696-fe0f","Advogado",52),("1f4bc","Assessor",53)]):
    emoji(c,200+k*340,Y,210,w(i)-0.05,16.22,pitch=1.0+k*0.12)
    label(lab,200+k*340,Y+175,w(i),16.22,small=True)
# 7 telefone + cadeado
emoji("1f4f1",540,Y,300,w(54)+0.05,18.88)
emoji("1f512",700,Y+70,160,w(59),18.88,anim="shake",sfx="lock")
label("Só ela tem acesso",540,LY,w(56),18.88)
# 8 drama: um dia essa pessoa falta
fx("grade",18.9,20.12,gray=0.85,dark=0.35)
sfx("boom",18.9,1.0,1.0)
# 9 meses procurando
emoji("1f4c5",340,Y,260,w(70),22.25,anim="flip")
emoji("1f50d",760,Y,230,w(73)-0.1,22.25,anim="search",pitch=1.2)
label("Meses procurando",540,LY,w(72),22.25,color="#E0364F")
# 10 dez minutos
emoji("23f1-fe0f",540,Y,280,w(75),24.4,anim="pop",ring=[w(77),24.2])
fx("bigtext",w(77),24.4,text="10 min",x=540,y=LY,size=96,pill="#16A34A")
sfx("tick",w(77)+0.2,1.0,0.6)
# 11 pior momento
emoji("26a0-fe0f",540,Y,290,w(83),26.65,anim="pulse")
fx("redglow",w(85),26.65)
label("No pior momento possível",540,LY,w(84),26.65,color="#E0364F")
fx("shake",w(85),w(85)+0.35,amp=10)
# 12 pasta
emoji("1f4c2",540,Y+10,340,w(90),30.65,anim="pop",sfx="whooshup",moveTo=[540,Y+40,w(92)-0.05,0.35,240])
fx("burst",w(91),w(91)+0.6,x=540,y=Y)
label("Faça uma pasta",540,LY,w(91),w(92)-0.05)
# 13 onde esta / com quem falar -> entram na pasta
emoji("1f4cd",260,Y-60,170,w(93),30.65,flyTo=[540,Y+40,30.25,0.35])
label("Onde está cada coisa",300,Y+135,w(94),30.25,small=True)
emoji("1f4de",860,Y-60,170,w(98),30.65,pitch=1.2,flyTo=[540,Y+40,30.32,0.35])
label("Com quem falar",800,Y+135,w(98),30.25,small=True)
sfx("swish",30.25,1.0,0.6)
# 14 lugar + confianca
emoji("1f511",360,Y,250,w(102),34.45)
emoji("1f91d",720,Y,260,w(104),34.45,pitch=1.2)
label("Alguém de confiança",540,LY,w(105),34.45)
# 15 acesso garantido
emoji("2705",540,Y,300,w(113),38.68,sfx="ding")
fx("burst",w(113),w(113)+0.7,x=540,y=Y)
label("Acesso garantido",540,LY,w(118),38.68,color="#16A34A")
# 16 se faltasse amanha
emoji("1f468-200d-1f469-200d-1f467-200d-1f466",360,Y,270,w(127),42.93)
emoji("1f9ed",760,Y,250,w(129),42.93,anim="spin",pitch=1.2)
label("Saberia por onde começar?",540,LY,w(126),42.93)
# 17 CTA
emoji("1f4ac",540,Y,300,w(135)-0.05,dur,anim="pulse",sfx="notify")
label("Me manda uma mensagem",540,LY,w(136),45.9,color="#7B2FF7")
emoji("1f5c2-fe0f",380,Y+10,0,0,0,sfx=None) if False else None
label("Vamos organizar isso ✓",540,LY,w(145),dur,color="#16A34A")
fx("arrow",w(137),dur,x=540,y=LY+120)
# transitions (segment boundaries)
WHIP={4.55,10.95,24.419,26.669,34.469,42.949,38.699}
TR=[]
for k in range(1,len(segs)):
    t=segs[k]["t"]
    if abs(t-18.9)<0.01: kind="dip"
    elif any(abs(t-x)<0.01 for x in WHIP): kind="whip"
    else: kind="punch"
    TR.append(dict(t=t,kind=kind,dir=(1 if k%2 else -1)))
    sfx({"whip":"whoosh","punch":"swish","dip":None}[kind] or "none",t,1.0+0.05*(k%3),0.45 if kind=="punch" else 1.0)
SFX=[s for s in SFX if s["kind"]!="none"]
json.dump(dict(duration=dur,segments=segs,words=words,elements=E,transitions=TR,sfx=sorted(SFX,key=lambda s:s["t"])),open(W+"/cues.json","w"),ensure_ascii=False,indent=0)
print("dur",dur,"elements",len(E),"sfx",len(SFX),"transitions",[(round(x['t'],2),x['kind']) for x in TR])
