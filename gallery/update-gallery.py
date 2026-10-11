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

try:
    from PIL import Image, ImageOps
except ImportError:
    print('✗ 需要 Pillow：pip install Pillow')
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'images' / 'gallery'
THUMBS = SRC / 'thumbs'
PAGE = ROOT / 'gallery' / 'index.html'

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
            'thumb': f'../images/gallery/thumbs/{thumb.name}',
            'full': f'../images/gallery/{path.name}',
            'caption': caption,
            'date': parse_date(caption),
        })

    # 有日期的在前、按时间倒序；没有日期的排在最后，按文件名
    dated = sorted((p for p in photos if p['date']), key=lambda p: p['date'], reverse=True)
    undated = sorted((p for p in photos if not p['date']), key=lambda p: p['full'])
    return dated + undated


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

    prune_thumbs({Path(p['full']).stem for p in photos})

    if not update_page(photos):
        return 1

    print(f'📷 共 {len(photos)} 张照片')
    for photo in photos:
        print(f"  • {photo['date'] or '          '} {photo['caption'] or '(无图注)'}")
    print('✅ 画廊更新完成！')

    return 0


if __name__ == '__main__':
    sys.exit(main())
