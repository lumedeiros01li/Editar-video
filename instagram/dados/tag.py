import sys, re, statistics as st
sys.path.insert(0,'.')
from load import *
L=[r for r in lucas() if r['type']=='Video' and r['plays']]
sets={'Bernardo':ref(BERNARDO),'Pedro':ref(PEDRO),'Artur':ref(ARTUR),'Lucas':L}
LUX=['hipismo','Helicóptero','Marina','Festa de 15','Rolex','Antártida','Rico x super','Proposta de R$ 30']
def tag(acc,r):
    h=r['hook']
    if acc=='Bernardo':
        if 'Me chama no direct' in h or 'comprar você' in h: return 'G venda/CTA'
        if any(k in h for k in ['acordo','opinião','Acha que dá','renda necessária']): return 'C dilema/pergunta'
        return 'H entretenimento/opinião social'
    if any(k in h for k in LUX): return 'A preço do luxo'
    if re.match(r'Pedro,',h): return 'C dilema/pergunta'
    if re.search(r'^(Custo de|Carteira de|Ortodontista|Clínica de implante)',h): return 'B raio-x de personagem'
    if acc=='Lucas' and re.search(r'\b(Um|Uma|Casal) (restaurante|casal|diretor|empresári|advogado|empresária)|^Casal|R\$ 60 mil por mês na conta|Sobrou R\$ 0|Afastado por 6|Achar que a empresa',h): return 'B raio-x de personagem'
    if re.search(r'em 2000|7 países|Nasdaq|2016, 2020|parou duas vezes|viagem de US',h): return 'D comparativo histórico'
    if re.search(r'Copom|eleição|Eleição|democratas|Primeiro turno|banco com 3 milhões|Lara Resende|Bom dia|51,8|Selic caiu|circuit breaker é|bolsa caiu',h,re.I): return 'E notícia/mercado'
    if re.search(r'link na bio|O link está na bio|Quer ser meu|Quer esse atendimento',r.get('cap','') or '') and acc!='Lucas': return 'G venda/CTA'
    if re.match(r'^(\d+|Oito|Sete) ',h) or re.search(r'^\d+ (coisas|erros|títulos|investimentos|perguntas|dicas)|As 10|esses 4',h): return 'F lista'
    if acc in('Pedro','Artur') and re.search(r'link na bio',h): return 'G venda/CTA'
    return 'I ensino/conta (outros)'
# CTA de venda do Pedro/Artur vem da legenda completa: marcar à mão
VENDA={'DfdGokTDxZK','DfX1-7eHV2k','DfZ175TkcI4','DfVKjv3Ajx7','DfUhh4mCGCt','DfYK5AenJmo','DfSrJkMyjvs','DfDgJFkj6M2'}
res={}
for acc,rows in sets.items():
    med=st.median([r['plays'] for r in rows])
    for r in rows:
        t='G venda/CTA' if r['code'] in VENDA else tag(acc,r)
        if acc=='Lucas' and r['date']<'2026-10-19': t=t  # mantém
        r['tag']=t; r['mult']=r['plays']/med
        res.setdefault(t,{}).setdefault(acc,[]).append(r)
for t in sorted(res):
    line=[f'{t:32}']
    for acc in ['Bernardo','Pedro','Artur','Lucas']:
        rs=res[t].get(acc,[])
        line.append(f"{acc[:2]} n={len(rs):2} mult={st.median([r['mult'] for r in rs]):4.1f}x" if rs else f"{acc[:2]} n= 0          ")
    print(' | '.join(line))
print()
for r in sorted(res.get('I ensino/conta (outros)',{}).get('Lucas',[]),key=lambda r:-r['plays'])[:40]:
    print(r['date'],r['plays'],round(r['dur']),r['hook'][:80])
