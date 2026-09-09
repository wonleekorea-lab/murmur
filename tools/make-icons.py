"""ひとりごと（murmur）のアイコンを生成する。

図案は「喋ったものが行になる」。押す白い丸と、そこから右へ伸びる3本の行。
行は下へ行くほど短い。アプリの中で実際に起きることと同じ形にしてある。

依存なしで動く（標準ライブラリのみ）。4倍のスーパーサンプリングで縁をなめらかにする。

    python3 tools/make-icons.py
"""

import math
import os
import struct
import zlib

# 呼び出したディレクトリに関係なく、リポジトリ直下へ書き出す
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# iOS Safari はホーム画面のアイコンを「URLごと」に長期キャッシュする。
# 絵を変えたらこの数字を上げ、参照側（shell-head.html / manifest.json / sw.js）も
# 揃えて書き換えること。同じファイル名のままでは端末に古い絵が残り続ける。
VERSION = 1
BG = (8, 8, 10)        # --void
FG = (250, 250, 247)   # --lume
SS = 4                 # 1辺あたりのサブサンプル数

# 位置・太さはすべて画像サイズに対する比で持つ（どのサイズでも同じ見え方になる）
DOT = (0.255, 0.500, 0.118)      # 丸の中心x, 中心y, 半径
BAR_X = 0.430                    # 行の左端
BAR_H = 0.052                    # 行の太さ
BARS = [                         # 中心y, 右端x, 濃さ
    (0.340, 0.815, 1.00),
    (0.500, 0.720, 0.62),
    (0.660, 0.588, 0.30),
]
R = BAR_H / 2.0                  # 行の角の丸み


def coverage(px, py, n):
    """その1点が白でどれだけ覆われるか（0.0〜1.0）を返す。"""
    x, y = px / n, py / n
    if math.hypot(x - DOT[0], y - DOT[1]) <= DOT[2]:
        return 1.0
    for cy, x2, op in BARS:
        # 角を丸めた横棒（両端は半円）
        cx = min(max(x, BAR_X + R), x2 - R)
        if math.hypot(x - cx, y - cy) <= R:
            return op
    return 0.0


def render(n):
    rows = []
    step = 1.0 / SS
    off = step / 2.0
    for py in range(n):
        row = bytearray()
        for px in range(n):
            a = 0.0
            for sy in range(SS):
                for sx in range(SS):
                    a += coverage(px + off + sx * step, py + off + sy * step, n)
            a /= SS * SS
            row.extend(int(round(BG[i] + (FG[i] - BG[i]) * a)) for i in range(3))
        rows.append(row)
    return rows


def write_png(n, path):
    raw = bytearray()
    for row in render(n):
        raw.append(0)      # フィルタなし
        raw.extend(row)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    print("%s  %dx%d  %d bytes" % (path, n, n, len(png)))


if __name__ == "__main__":
    for size in (180, 192, 512):
        write_png(size, "%s/icon-%d-v%d.png" % (OUT, size, VERSION))
