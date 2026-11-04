from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
p=Path(r'C:\Users\Veronika\Documents\Codex\2026-10-27\db\outputs\SportsResultsLab07\report\rendered')
files=sorted(p.glob('page-*.png'),key=lambda x:int(x.stem.split('-')[1]))
thumbs=[]
for f in files:
 im=Image.open(f).convert('RGB'); im.thumbnail((360,470)); canvas=Image.new('RGB',(380,505),'#dce2ea'); canvas.paste(im,((380-im.width)//2,8)); ImageDraw.Draw(canvas).text((14,480),f.name,fill='black'); thumbs.append(canvas)
out=Image.new('RGB',(380*3,505*((len(thumbs)+2)//3)),'white')
for i,im in enumerate(thumbs): out.paste(im,((i%3)*380,(i//3)*505))
out.save(p/'contact_sheet.png')
