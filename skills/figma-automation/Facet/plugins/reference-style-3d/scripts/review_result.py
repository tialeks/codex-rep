#!/usr/bin/env python3
"""Validate PNG and hash-bound review evidence; never approve artistic quality."""
import argparse
import hashlib
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import json
from pathlib import Path
import struct
import zlib
from prepare_generation import verify

STATUSES = {'pass', 'limited', 'fail'}
CHECKS = {'form', 'materials', 'light', 'composition', 'colors', 'style_fidelity'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decode_png(path):
    """Decode standard non-interlaced PNG scanlines, including palette/tRNS alpha.

    Pillow handles normal PNG pixels; the exact 16-bit fallback preserves alpha precision.
    """
    data = Path(path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Result is not a PNG')
    offset, chunks, ended = 8, [], False
    while offset < len(data):
        if offset + 12 > len(data): raise ValueError('Truncated PNG chunk')
        size = struct.unpack('>I', data[offset:offset+4])[0]
        kind = data[offset+4:offset+8]
        end = offset + 12 + size
        if end > len(data): raise ValueError('Truncated PNG payload')
        payload = data[offset+8:offset+8+size]
        crc = struct.unpack('>I', data[offset+8+size:end])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc: raise ValueError('PNG CRC mismatch')
        chunks.append((kind, payload)); offset = end
        if kind == b'IEND':
            if size: raise ValueError('Invalid PNG IEND')
            ended = True; break
    if not ended or offset != len(data): raise ValueError('PNG missing end or trailing data')
    if not chunks or chunks[0][0] != b'IHDR' or len(chunks[0][1]) != 13: raise ValueError('Invalid PNG header')
    if sum(k == b'IHDR' for k, _ in chunks) != 1: raise ValueError('Duplicate PNG header')
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', chunks[0][1])
    allowed = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
    if not width or not height or width*height > 64000000: raise ValueError('PNG dimensions unsupported')
    if color not in allowed or depth not in allowed[color] or compression or filtering: raise ValueError('Unsupported PNG encoding')
    if interlace not in (0,1): raise ValueError('Invalid PNG interlace')
    if interlace and depth == 16: raise ValueError('16-bit Adam7 PNG is not supported')
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    row_size = (width*channels*depth + 7)//8
    expected = (row_size+1)*height
    if interlace:
        expected = 0
        for x,y,dx,dy in ((0,0,8,8),(4,0,8,8),(0,4,4,8),(2,0,4,4),(0,2,2,4),(1,0,2,2),(0,1,1,2)):
            pw,ph = max(0,(width-x+dx-1)//dx),max(0,(height-y+dy-1)//dy)
            if pw and ph: expected += (((pw*channels*depth+7)//8)+1)*ph
    if expected > 512000000: raise ValueError('PNG decoded size too large')
    allowed_critical = {b'IHDR', b'PLTE', b'IDAT', b'IEND'}
    if any(k[:1].isupper() and k not in allowed_critical for k,_ in chunks): raise ValueError('Unknown critical PNG chunk')
    for singleton in (b'PLTE', b'tRNS'):
        if sum(k == singleton for k,_ in chunks)>1: raise ValueError('Duplicate PNG palette/transparency')
    kinds=[k for k,_ in chunks]
    if b'IDAT' not in kinds: raise ValueError('Missing PNG image data')
    first,last=kinds.index(b'IDAT'),len(kinds)-1-kinds[::-1].index(b'IDAT')
    if any(k!=b'IDAT' for k in kinds[first:last+1]): raise ValueError('Non-contiguous PNG image data')
    if any(k in (b'PLTE',b'tRNS') for k in kinds[first:]): raise ValueError('PNG palette/transparency after pixels')
    palette = next((p for k,p in chunks if k == b'PLTE'), b'')
    transparency = next((p for k,p in chunks if k == b'tRNS'), b'')
    if color == 3 and (not palette or len(palette)%3): raise ValueError('Invalid PNG palette')
    if transparency and (color in (4,6) or (color == 0 and len(transparency)!=2) or (color == 2 and len(transparency)!=6) or (color == 3 and len(transparency)>len(palette)//3)):
        raise ValueError('Invalid PNG transparency')
    compressed = b''.join(p for k, p in chunks if k == b'IDAT')
    decoder = zlib.decompressobj()
    try: raw = decoder.decompress(compressed, expected+1)
    except zlib.error as exc: raise ValueError('PNG compressed data invalid') from exc
    if len(raw) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('PNG scanline size/stream mismatch')
    # Decode ordinary PNGs in native code instead of a Python loop per channel.
    if depth != 16:
        try:
            with Image.open(BytesIO(data)) as im:
                im.load()
                if color == 3 and any(im.histogram()[len(palette)//3:]):
                    raise ValueError('PNG palette index invalid')
                histogram = im.convert('RGBA').getchannel('A').histogram()
        except (OSError, SyntaxError, UnidentifiedImageError) as exc:
            raise ValueError('PNG pixels invalid: '+str(exc)) from exc
        return {'width': width, 'height': height, 'bitDepth': depth,
                'colorType': color, 'nonopaquePixels': sum(histogram[:255])}

    # Pillow converts 16-bit RGBA to 8-bit. Retain exact transparency counting
    # for those uncommon files so almost-opaque alpha is not rounded away.
    bpp = max(1, (channels*depth+7)//8); previous = bytearray(row_size); nonopaque = 0
    for y in range(height):
        start = y*(row_size+1); filter_type = raw[start]; row = bytearray(raw[start+1:start+1+row_size])
        if filter_type > 4: raise ValueError('Invalid PNG filter')
        for i in range(row_size):
            a = row[i-bpp] if i>=bpp else 0; b = previous[i]; c = previous[i-bpp] if i>=bpp else 0
            if filter_type == 1: predictor = a
            elif filter_type == 2: predictor = b
            elif filter_type == 3: predictor = (a+b)//2
            elif filter_type == 4:
                p=a+b-c; da,db,dc=abs(p-a),abs(p-b),abs(p-c)
                predictor = a if da<=db and da<=dc else b if db<=dc else c
            else: predictor = 0
            row[i] = (row[i]+predictor)&255
        if depth == 16: values = struct.unpack('>'+str(width*channels)+'H', row)
        elif depth == 8: values = row
        else: values = [(row[(i*depth)//8] >> (8-depth-(i*depth)%8)) & ((1<<depth)-1) for i in range(width*channels)]
        maximum = (1<<depth)-1
        if color in (4,6): nonopaque += sum(values[x*channels+channels-1] < maximum for x in range(width))
        elif color == 3:
            if any(v >= len(palette)//3 for v in values): raise ValueError('PNG palette index invalid')
            nonopaque += sum(v < len(transparency) and transparency[v] < 255 for v in values)
        elif transparency:
            transparent = struct.unpack('>'+str(channels)+'H', transparency)
            nonopaque += sum(tuple(values[x*channels:(x+1)*channels]) == transparent for x in range(width))
        previous = row
    return {'width': width, 'height': height, 'bitDepth': depth, 'colorType': color, 'nonopaquePixels': nonopaque}


def validate(execution, file, review_file, expected_manifest_sha256, *, allow_failed_output=False):
    execution, file, review_file = Path(execution), Path(file).resolve(), Path(review_file)
    args = verify(execution, expected_manifest_sha256)
    receipt = json.loads((execution/'submission.json').read_text())
    if receipt.get('manifestSha256') != expected_manifest_sha256: raise ValueError('Receipt manifest binding differs')
    if receipt.get('arguments') != args: raise ValueError('Receipt arguments differ')
    observed = receipt.get('observedHandle', {})
    result_sha = digest(file)
    if observed.get('type') != 'generated-artifact' or observed.get('sha256') != result_sha:
        raise ValueError('Receipt must bind this generated artifact SHA; call-only receipt is insufficient')
    png = decode_png(file)
    transparency_mismatch = bool(args.get('transparent_background') and png['nonopaquePixels'] == 0)
    if transparency_mismatch and not allow_failed_output: raise ValueError('Requested transparency but PNG is fully opaque')
    review = json.loads(review_file.read_text())
    if not isinstance(review,dict) or review.get('status') not in STATUSES: raise ValueError('Invalid review status')
    if transparency_mismatch and review.get('status') != 'fail': raise ValueError('Opaque output for requested transparency requires fail review')
    if review.get('sha256') != result_sha: raise ValueError('Review SHA differs from result')
    if not isinstance(review.get('file'),str) or Path(review['file']).resolve()!=file: raise ValueError('Review file differs from result')
    checks = review.get('checks')
    if not isinstance(checks,dict) or not CHECKS.issubset(checks): raise ValueError('Missing required review checks: '+', '.join(sorted(CHECKS)))
    manifest = json.loads((execution/'manifest.json').read_text())
    settings = manifest.get('request', {}).get('settings') or {}
    facets = (settings.get('reference') or {}).get('facets', [])
    missing = {'reference_'+facet for facet in facets} - checks.keys()
    if missing: raise ValueError('Missing selected reference checks: '+', '.join(sorted(missing)))
    for name, check in checks.items():
        if not isinstance(check,dict) or check.get('status') not in STATUSES: raise ValueError('Invalid check status: '+name)
        observation = check.get('observation')
        if not isinstance(observation,str) or len(observation.strip()) < 20 or observation.strip().lower() in ('pass','ok','looks good','todo','not checked'):
            raise ValueError('Concrete observation required: '+name)
    if any(c['status']=='fail' for c in checks.values()) and review['status']!='fail': raise ValueError('Any failed check requires overall fail')
    if review['status']=='pass' and any(c['status']!='pass' for c in checks.values()): raise ValueError('Overall pass contradicts limited/failed checks')
    return {'evidenceValid':True,'artisticApproval':False,'reviewStatus':review['status'],'sha256':result_sha,'png':png,'limitation':'Structural validation cannot judge whether prose is true or visually specific. Limited/fail reviews remain limited/fail.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('execution','file','review','expected-manifest-sha256'): parser.add_argument('--'+arg,required=True)
    args=parser.parse_args()
    try: result=validate(args.execution,args.file,args.review,args.expected_manifest_sha256)
    except (ValueError,KeyError,TypeError,OSError) as exc: parser.exit(1,str(exc)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
