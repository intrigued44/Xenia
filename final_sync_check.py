import os

base_src = r'C:\Users\pranav\Downloads\nous-windows-installer-src'
base_dist = r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\dist\win-unpacked\resources\xenia_server\_internal'

files = [
    ('client/db.py', 'client/db.py'),
    ('platform_core/server.py', 'platform_core/server.py'),
    ('platform_core/intelligence/skills_engine.py', 'platform_core/intelligence/skills_engine.py'),
]

print('=== Backend file sync check ===')
all_ok = True
for src_rel, dist_rel in files:
    src = os.path.join(base_src, src_rel.replace('/', os.sep))
    dist = os.path.join(base_dist, dist_rel.replace('/', os.sep))
    s1 = os.path.getsize(src)
    s2 = os.path.getsize(dist)
    match = s1 == s2
    if not match:
        all_ok = False
    status = 'OK' if match else 'MISMATCH'
    name = src_rel.split('/')[-1]
    print(f'  {name}: src={s1:,}b dist={s2:,}b [{status}]')

print()
print('=== ASAR check ===')
asar = r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\dist\win-unpacked\resources\app.asar'
print(f'  app.asar: {os.path.getsize(asar):,} bytes')

html_src_size = os.path.getsize(os.path.join(base_src, 'ui', 'index.html'))
html_asar_size = os.path.getsize(r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\dist\asar-extracted\index.html')
match = html_src_size == html_asar_size
if not match:
    all_ok = False
print(f'  index.html: src={html_src_size:,}b asar-copy={html_asar_size:,}b [{"OK" if match else "MISMATCH"}]')

print()
print('RESULT: ' + ('All files in sync!' if all_ok else 'SOME FILES OUT OF SYNC - manual copy needed'))
