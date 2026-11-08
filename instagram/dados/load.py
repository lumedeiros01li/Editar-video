import json, statistics as st
from refs import *
def lucas():
    d=json.load(open('lucas_posts_2026-11-08.json'))['items']
    rows=[]
    for it in d:
        cap=it.get('caption') or ''
        rows.append(dict(code=it['shortCode'], date=it['timestamp'][:10], type=it['type'],
            plays=it.get('videoPlayCount'), likes=it.get('likesCount',0), com=it.get('commentsCount',0),
            dur=it.get('videoDuration'), orig=it.get('musicInfo.uses_original_audio'),
            hook=cap.split('\n')[0].strip(), cap=cap))
    # reel de 04/09 que veio só na coleta de reels
    rows.append(dict(code='Dc3VoPsBLnt',date='2026-09-04',type='Video',plays=1867,likes=31,com=7,dur=8.3,orig=True,
        hook='Pouca gente calcula isso, mas quando alguém falece, antes de qualquer herdeiro receber os bens, o estado cobra ITCMD.',cap='ITCMD ... Manda "ITCMD" no direct'))
    return rows
def ref(name):
    return [dict(code=c,date='2026-'+d,plays=p,likes=l,com=cm,dur=du,hook=h) for c,d,p,l,cm,du,h in name]
