#!/usr/bin/env python3
"""
画廊内容更新脚本
扫描 images/gallery/ 下的照片，读取同名 .md 文件作为图注，
生成网页用缩略图，并把静态数据写入 gallery/index.html。
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote

try:
    from PIL import Image, ImageOps
except ImportError:
    print('✗ 需要 Pillow：pip install Pillow')
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'images' / 'gallery'
THUMBS = SRC / 'thumbs'
PAGE = ROOT / 'gallery' / 'index.html'
ORDER_FILE = SRC / 'order.txt'

PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
THUMB_LONG_EDGE = 700
THUMB_QUALITY = 82

# 图注可以以日期开头，如 2026.10.05 / 2026-10-05 / 2026/10/5，用于排序
DATE_RE = re.compile(r'^\s*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})')


def read_caption(stem):
    """同名的 .md 文件整篇作为图注，空白折叠成一行。没有则返回 None。"""
    md = SRC / f'{stem}.md'
    if not md.exists():
        return None
    return ' '.join(md.read_text(encoding='utf-8').split())


def parse_date(caption):
    """从图注开头解析日期，用于排序；解析不出则返回 None。"""
    if not caption:
        return None
    m = DATE_RE.match(caption)
    if not m:
        return None
    year, month, day = (int(g) for g in m.groups())
    return f'{year:04d}-{month:02d}-{day:02d}'


def make_thumb(path, out):
    """缩略图缺失或比源文件旧时才重新生成（可重复运行）。"""
    if out.exists() and out.stat().st_mtime >= path.stat().st_mtime:
        return False

    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)  # 手机照片的旋转信息存在 EXIF 里
        im = im.convert('RGB')

        width, height = im.size
        scale = THUMB_LONG_EDGE / max(width, height)
        if scale < 1:
            im = im.resize(
                (max(1, round(width * scale)), max(1, round(height * scale))),
                Image.LANCZOS,
            )

        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out, 'JPEG', quality=THUMB_QUALITY, optimize=True, progressive=True)

    return True


def collect():
    """扫出所有照片，生成缩略图，返回按时间倒序排列的数据。"""
    photos = []

    for path in sorted(SRC.iterdir()):
        if not path.is_file() or path.suffix.lower() not in PHOTO_EXTS:
            continue

        stem = path.stem
        caption = read_caption(stem)
        if caption is None:
            print(f'⚠ 缺少图注: {path.name}（可以创建 {stem}.md 来添加）')
            caption = ''

        thumb = THUMBS / f'{stem}.jpg'
        if make_thumb(path, thumb):
            print(f'✓ 生成缩略图: {thumb.relative_to(ROOT)}')

        photos.append({
            # 文件名里的空格、中文等要转义成 URL 形式
            'thumb': quote(f'../images/gallery/thumbs/{thumb.name}'),
            'full': quote(f'../images/gallery/{path.name}'),
            'caption': caption,
            'date': parse_date(caption),
        })

    return photos


def read_order():
    """order.txt 里一行一个文件名，按从上到下的顺序排；# 开头的行是注释。"""
    if not ORDER_FILE.exists():
        return []
    return [
        line.strip()
        for line in ORDER_FILE.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.strip().startswith('#')
    ]


def source_name(photo):
    """从转义过的 URL 反推出磁盘上的真实文件名。"""
    return unquote(photo['full']).rsplit('/', 1)[-1]


def sort_photos(photos, order):
    """order.txt 里列出的按列表顺序排在前面，其余按日期倒序接在后面。"""
    def by_date(items):
        dated = sorted((p for p in items if p['date']), key=lambda p: p['date'], reverse=True)
        undated = sorted((p for p in items if not p['date']), key=lambda p: p['full'])
        return dated + undated

    if not order:
        return by_date(photos)

    rank = {name: i for i, name in enumerate(order)}
    present = {source_name(p) for p in photos}
    for name in order:
        if name not in present:
            print(f'⚠ order.txt 里的 {name} 没有对应照片，已忽略')

    listed = sorted(
        (p for p in photos if source_name(p) in rank),
        key=lambda p: rank[source_name(p)],
    )
    unlisted = [p for p in photos if source_name(p) not in rank]
    return listed + by_date(unlisted)


def prune_thumbs(keep_stems):
    """删掉源照片已经不在的缩略图。"""
    if not THUMBS.exists():
        return
    for stale in sorted(THUMBS.iterdir()):
        if stale.is_file() and stale.stem not in keep_stems:
            stale.unlink()
            print(f'✓ 删除多余缩略图: {stale.name}')


def update_page(photos):
    """把照片数据写回 gallery/index.html。"""
    if not PAGE.exists():
        print(f'✗ 找不到 {PAGE.relative_to(ROOT)}')
        return False

    # json 的带引号键值在 JS 里同样合法，且能正确处理引号与中文
    body = json.dumps(photos, ensure_ascii=False, indent=2).splitlines()
    array = 'const galleryPhotos = {}\n{};'.format(
        body[0],
        '\n'.join('    ' + line for line in body[1:]),
    )

    content = PAGE.read_text(encoding='utf-8')
    new_content, count = re.subn(
        r'const galleryPhotos = \[[\s\S]*?\];',
        lambda _match: array,  # 用函数替换，避免反斜杠被当成转义
        content,
        count=1,
    )

    if count == 0:
        print('✗ 在 gallery/index.html 里找不到 galleryPhotos 数组')
        return False

    if new_content != content:
        PAGE.write_text(new_content, encoding='utf-8')
        print(f'✓ 更新 {PAGE.relative_to(ROOT)}')
    else:
        print(f'✓ {PAGE.relative_to(ROOT)} 已是最新')

    return True


def main():
    print('🔄 开始更新画廊...')

    if not SRC.exists():
        print(f'✗ 目录不存在: {SRC.relative_to(ROOT)}')
        return 1

    photos = collect()
    if not photos:
        print(f'❌ {SRC.relative_to(ROOT)} 里没有找到照片')
        return 1

    photos = sort_photos(photos, read_order())

    # 用磁盘上的真实文件名，不能用上面转义过的 URL
    keep_stems = {
        p.stem for p in SRC.iterdir()
        if p.is_file() and p.suffix.lower() in PHOTO_EXTS
    }
    prune_thumbs(keep_stems)

    if not update_page(photos):
        return 1

    print(f'📷 共 {len(photos)} 张照片')
    for photo in photos:
        print(f"  • {photo['date'] or '          '} {photo['caption'] or '(无图注)'}")
    print('✅ 画廊更新完成！')

    return 0


if __name__ == '__main__':
    sys.exit(main())
