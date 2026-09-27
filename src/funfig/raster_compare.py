"""Small PNG/PGM reader and normalized raster comparison for topology candidates."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


class RasterError(ValueError):
    pass


def read_gray_image(path: str | Path) -> list[list[int]]:
    source = Path(path)
    try:
        if source.stat().st_size > 64*1024*1024:
            raise RasterError("reference image exceeds 64 MiB")
        data = source.read_bytes()
    except OSError as exc:
        raise RasterError(f"cannot read reference image: {source}") from exc
    if data.startswith(b"P5"):
        position = 2
        tokens = []
        while len(tokens) < 3:
            if position >= len(data):
                raise RasterError("PGM header is incomplete")
            while data[position:position+1] in (b" ", b"\n", b"\r", b"\t"):
                position += 1
                if position >= len(data):
                    raise RasterError("PGM header is incomplete")
            if data[position:position+1] == b"#":
                try: position = data.index(b"\n", position) + 1
                except ValueError as exc: raise RasterError("PGM comment is unterminated") from exc
                continue
            end = position
            while end < len(data) and data[end:end+1] not in (b" ", b"\n", b"\r", b"\t"):
                end += 1
            if end == len(data):
                raise RasterError("PGM header is incomplete")
            tokens.append(int(data[position:end]))
            position = end
        width, height, maximum = tokens
        position += 2 if data[position:position+2] == b"\r\n" else 1
        if maximum != 255 or not 0 < width <= 4096 or not 0 < height <= 4096 or len(data[position:]) < width*height:
            raise RasterError("PGM must be 8-bit and at most 4096 pixels per side")
        pixels = data[position:position+width*height]
        return [list(pixels[row*width:(row+1)*width]) for row in range(height)]
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RasterError("reference image must be an 8-bit PNG or binary PGM")
    position = 8
    idat = bytearray()
    width = height = color = interlace = None
    palette = b""
    transparency = b""
    while position + 12 <= len(data):
        length = struct.unpack_from(">I", data, position)[0]
        if position + 12 + length > len(data):
            raise RasterError("PNG chunk is truncated")
        tag = data[position+4:position+8]
        chunk = data[position+8:position+8+length]
        position += 12 + length
        if tag == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            if depth != 8 or color not in (0, 2, 3, 4, 6) or interlace != 0 or not 0 < width <= 4096 or not 0 < height <= 4096:
                raise RasterError("PNG must be non-interlaced 8-bit and at most 4096 pixels per side")
        elif tag == b"PLTE": palette = chunk
        elif tag == b"tRNS": transparency = chunk
        elif tag == b"IDAT": idat.extend(chunk)
        elif tag == b"IEND": break
    if width is None:
        raise RasterError("PNG has no IHDR")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    stride = width * channels
    expected = height*(stride+1)
    try:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(idat, expected+1)
    except zlib.error as exc: raise RasterError("PNG image data is corrupt") from exc
    if len(raw) != expected or not decoder.eof:
        raise RasterError("PNG scanline size is invalid")
    rows = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        row = bytearray(raw[offset:offset+stride])
        offset += stride
        for index in range(stride):
            left = row[index-channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index-channels] if index >= channels else 0
            if filter_type == 1: predictor = left
            elif filter_type == 2: predictor = up
            elif filter_type == 3: predictor = (left+up)//2
            elif filter_type == 4:
                p = left+up-upper_left
                distances = (abs(p-left), abs(p-up), abs(p-upper_left))
                predictor = (left, up, upper_left)[distances.index(min(distances))]
            elif filter_type == 0: predictor = 0
            else: raise RasterError("PNG has unsupported scanline filter")
            row[index] = (row[index]+predictor) & 255
        gray = []
        for index in range(0, stride, channels):
            if color == 0: value, alpha = row[index], 255
            elif color == 4: value, alpha = row[index], row[index+1]
            elif color == 3:
                entry = row[index]
                if 3*entry+2 >= len(palette): raise RasterError("PNG palette index is invalid")
                rgb = palette[3*entry:3*entry+3]
                value = (54*rgb[0]+183*rgb[1]+19*rgb[2])//256
                alpha = transparency[entry] if entry < len(transparency) else 255
            else:
                rgb = row[index:index+3]
                value = (54*rgb[0]+183*rgb[1]+19*rgb[2])//256
                alpha = row[index+3] if color == 6 else 255
            gray.append((value*alpha + 255*(255-alpha))//255)
        rows.append(gray)
        previous = row
    return rows


def normalized_ink(image: list[list[int]], size: int = 160) -> list[float]:
    height, width = len(image), len(image[0])
    left, top, right, bottom = width, height, -1, -1
    for y, row in enumerate(image):
        for x, value in enumerate(row):
            if value < 248:
                left, top = min(left, x), min(top, y)
                right, bottom = max(right, x), max(bottom, y)
    if right < 0:
        raise RasterError("reference image contains no visible dark geometry")
    # Center in a square crop so aspect ratio survives comparison.
    span = max(right-left+1, bottom-top+1)
    cx, cy = (left+right)/2, (top+bottom)/2
    result = []
    for j in range(size):
        y = round(cy + (j/(size-1)-0.5)*span)
        for i in range(size):
            x = round(cx + (i/(size-1)-0.5)*span)
            value = image[y][x] if 0 <= x < width and 0 <= y < height else 255
            result.append(max(0.0, (248-value)/248))
    return result


def ink_distance(reference: list[float], candidate: list[float]) -> float:
    if len(reference) != len(candidate):
        raise RasterError("raster dimensions differ")
    return sum((a-b)**2 for a, b in zip(reference, candidate))/len(reference)
