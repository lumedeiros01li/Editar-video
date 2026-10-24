import sys
from PIL import Image
fs=sys.argv[2:]; out=sys.argv[1]
ims=[Image.open(f).resize((540,960)) for f in fs]
cols=min(len(ims), 5); rows=(len(ims)+cols-1)//cols
o=Image.new('RGB',(540*cols,960*rows),'white')
for i,im in enumerate(ims): o.paste(im,((i%cols)*540,(i//cols)*960))
o.save(out)
