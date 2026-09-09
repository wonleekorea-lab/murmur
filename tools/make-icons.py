"""鉱脈（vein）のアイコンを生成する。

図案はアプリの真ん中と同じ、平らなアメーバ。そこに脈が1本、通り抜けている。
声（かたち）と、その中に走っている筋（洞察）を、線1本で重ねた形。

脈はアメーバの中では地の色に反転する。塗りは2色だけで、影もグラデーションも使わない。

地は紙（アプリと同じ #F4F2EE）、脈は墨（#14120F）。アプリと同じで、色は使わない。
ember や aloud が黒地なので、ホーム画面で並んだときに見分けがつく。

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
VERSION = 2
BG = (244, 242, 238)   # --void  紙
FG = (20, 18, 15)      # --lume  墨
SS = 4                 # 1辺あたりのサブサンプル数

# アメーバ（アプリの真ん中と同じ考え方で、半径が角度ごとに揺れる閉じた形）
BLOB_R = 0.285

# 脈。アメーバを斜めに貫く1本と、短い枝1本だけ
VEINS = [
    ([(-0.45, 0.31), (-0.16, 0.11), (0.17, -0.12), (0.45, -0.31)],
     [0.007, 0.022, 0.022, 0.007]),
    ([(0.17, -0.12), (0.25, -0.36)], [0.016, 0.006]),
]


def blob_r(th):
    return BLOB_R * (1.0
                     + 0.090 * math.sin(3.0 * th + 1.7)
                     + 0.055 * math.sin(5.0 * th + 2.9)
                     + 0.030 * math.sin(2.0 * th + 0.8))


def seg_hit(px, py, a, b, wa, wb):
    """折れ線の1区間に、その点が入っているか（半幅は端から端へ線形に細る）。"""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 <= 0:
        return False
    t = ((px - ax) * dx + (py - ay) * dy) / L2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    cx, cy = ax + dx * t, ay + dy * t
    return math.hypot(px - cx, py - cy) <= wa + (wb - wa) * t


def coverage(x, y, n):
    """墨で覆われるか。アメーバの内と脈は、重なったところで入れ替わる（XOR）。"""
    c = (n - 1) / 2.0
    px = (x - c) / n
    py = (y - c) / n
    inside = math.hypot(px, py) <= blob_r(math.atan2(py, px))
    on = False
    for pts, ws in VEINS:
        for i in range(len(pts) - 1):
            if seg_hit(px, py, pts[i], pts[i + 1], ws[i], ws[i + 1]):
                on = True
                break
        if on:
            break
    return 1.0 if inside != on else 0.0


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


def png(path, rows, n):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


for size in (180, 192, 512):
    name = "icon-%d-v%d.png" % (size, VERSION)
    png(os.path.join(OUT, name), render(size), size)
    print("wrote", name)
