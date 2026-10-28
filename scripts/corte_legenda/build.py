import json, re
keep=json.load(open("keep.json"))
words=[w for s in json.load(open("tr.json")) for w in s["words"]]
# mapa fonte -> saída
cum=[];t=0
for s,e in keep: cum.append((s,e,t)); t+=e-s
TOTAL=t
def mp(x):
    for s,e,o in cum:
        if s<=x<=e: return o+x-s
    # dentro de trecho cortado: vai para o próximo início
    for s,e,o in cum:
        if x<s: return o
    return TOTAL
# palavras (corrigidas à mão onde as duas transcrições divergem)
W=[]
for w in words:
    W.append([w["w"].strip(),w["s"],w["e"]])
fix=[]; i=0
while i<len(W):
    t_,s,e=W[i]
    if t_=="Bem": fix.append(["Vem",s,W[i][2]]); i+=1; continue
    if t_=="que" and W[i+1][0]=="vê": fix.append(["ver",s,W[i+1][2]]); i+=2; continue
    if t_=="estudo": fix.append(["isso",s,e]); fix.append(["tudo",(s+e)/2,e]) if False else None; i+=1; continue
    if re.fullmatch(r"\d+",t_) and i+1<len(W) and re.fullmatch(r"\.\d+,?",W[i+1][0]):
        fix.append([t_+W[i+1][0],s,W[i+1][2]]); i+=2; continue
    fix.append([t_,s,e]); i+=1
W=fix
# "isso aqui" -> "isso tudo aqui"
out=[]
for k,(t_,s,e) in enumerate(W):
    out.append([t_,s,e])
    if t_=="isso" and k+1<len(W) and W[k+1][0]=="aqui,":
        out[-1]=["isso",s,(s+W[k+1][1])/2]; out.append(["tudo",(s+W[k+1][1])/2,W[k+1][1]])
W=out
W=[w for w in W if not (w[1]>=54.8)]
# remover "ainda" duplicados etc: nada
# tempos na saída
for w in W:
    w[1]=mp(w[1])
# fim de cada palavra = início da próxima (limitado)
for k in range(len(W)):
    nxt=W[k+1][1] if k+1<len(W) else TOTAL
    W[k][2]=min(max(nxt,W[k][1]+0.12),W[k][1]+0.9) if k+1<len(W) else TOTAL
    if W[k][2]>nxt: W[k][2]=nxt if nxt>W[k][1] else W[k][1]+0.05
json.dump({"words":W,"total":TOTAL,"switch":mp(8.61)},open("words_out.json","w"),ensure_ascii=False)
print("duração",round(TOTAL,2),"troca de fundo em",round(mp(8.61),2))
print(" ".join(f"{w[0]}@{w[1]:.2f}" for w in W))
