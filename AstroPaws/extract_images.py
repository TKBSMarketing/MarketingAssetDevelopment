from pypdf import PdfReader
from PIL import Image
import os, io

reader = PdfReader(r'a:\TKBS Marketing - Git\MarketingAssetDevelopment\AstroPaws\Astro Paws Rulebook v4.pdf')
print(f'Pages: {len(reader.pages)}')

out_dir = r'a:\TKBS Marketing - Git\MarketingAssetDevelopment\AstroPaws\assets\extracted'
os.makedirs(out_dir, exist_ok=True)

count = 0
for page_num, page in enumerate(reader.pages):
    if '/XObject' in page['/Resources']:
        xobjects = page['/Resources']['/XObject'].get_object()
        for obj_name in xobjects:
            obj = xobjects[obj_name].get_object()
            if obj['/Subtype'] == '/Image':
                width = obj['/Width']
                height = obj['/Height']
                color_space = obj.get('/ColorSpace', 'unknown')
                filters = obj.get('/Filter', 'none')
                print(f'Page {page_num+1}, {obj_name}: {width}x{height}, Filter={filters}')

                try:
                    data = obj.get_data()
                    clean_name = obj_name.replace('/', '')

                    if filters == '/DCTDecode':
                        filepath = os.path.join(out_dir, f'page{page_num+1}_{clean_name}_{width}x{height}.jpg')
                        with open(filepath, 'wb') as f:
                            f.write(data)
                        print(f'  -> Saved: {filepath}')
                    else:
                        filepath = os.path.join(out_dir, f'page{page_num+1}_{clean_name}_{width}x{height}.png')
                        cs = str(color_space)
                        if 'RGB' in cs:
                            mode = 'RGB'
                        elif 'CMYK' in cs:
                            mode = 'CMYK'
                        else:
                            mode = 'RGB'
                        try:
                            img = Image.frombytes(mode, (width, height), data)
                            img.save(filepath)
                            print(f'  -> Saved: {filepath}')
                        except Exception as e:
                            print(f'  -> PIL error: {e}')
                    count += 1
                except Exception as e:
                    print(f'  -> Extract error: {e}')

print(f'\nTotal images found: {count}')
