import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from prepare_generation import ROOT, prepare, verify
from review_result import CHECKS, decode_png, digest, validate


def chunk(kind,payload):
    return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)


def png(alpha=255):
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(bytes([0,20,40,60,alpha])))+chunk(b'IEND',b'')


class ReviewResultTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.execution=self.base/'exec'
        s=dict(topic='Phone',mode='icon',count=1,objects=1,camera='front',size=32,detailMode='auto',detail=3,creativity=3,whiteBase=False,metal=20,pearl=10,background='transparent',palette='natural',effects=[],recognizable=True)
        m=prepare(ROOT,dict(schemaVersion=1,settings=s,prompt='A phone.'),self.execution);self.pin=m['manifestSha256']
        self.file=self.base/'result.png';self.file.write_bytes(png(0));self.review=self.base/'review.json'
        self.data=dict(status='limited',file=str(self.file),sha256=digest(self.file),checks={k:dict(status='pass',observation='Observed distinct subject surfaces and readable silhouettes.') for k in CHECKS})
        self.bind()

    def tearDown(self): self.tmp.cleanup()

    def bind(self):
        self.data['sha256']=digest(self.file);self.review.write_text(json.dumps(self.data))
        (self.execution/'submission.json').write_text(json.dumps(dict(manifestSha256=self.pin,arguments=verify(self.execution,self.pin),observedHandle=dict(type='generated-artifact',sha256=digest(self.file),id=str(self.file)))))

    def runcheck(self):return validate(self.execution,self.file,self.review,self.pin)

    def test_limited_remains_limited(self):
        result=self.runcheck();self.assertTrue(result['evidenceValid']);self.assertFalse(result['artisticApproval']);self.assertEqual(result['reviewStatus'],'limited');self.assertEqual(result['png']['nonopaquePixels'],1)

    def test_fail_review_is_valid_evidence_not_approval(self):
        self.data['status']='fail';self.data['checks']['form']['status']='fail';self.bind();self.assertEqual(self.runcheck()['reviewStatus'],'fail')

    def test_failed_check_requires_overall_fail_even_when_limited(self):
        self.data['status']='limited';self.data['checks']['form']['status']='fail';self.bind()
        with self.assertRaisesRegex(ValueError,'requires overall fail'):self.runcheck()

    def test_missing_review_or_result(self):
        self.review.unlink()
        with self.assertRaises(OSError):self.runcheck()
        self.bind();self.file.unlink()
        with self.assertRaises(OSError):self.runcheck()

    def test_foreign_result_rejected(self):
        self.file.write_bytes(png(10))
        with self.assertRaisesRegex(ValueError,'Receipt'):self.runcheck()

    def test_malformed_png_even_when_hashes_match(self):
        for content in [b'not PNG',png()[:-1],png()[:44]+b'bad',b'\x89PNG\r\n\x1a\n']:
            self.file.write_bytes(content);self.bind()
            with self.assertRaises(ValueError):self.runcheck()

    def test_fully_opaque_rejected_when_transparent_requested(self):
        self.file.write_bytes(png(255));self.bind()
        with self.assertRaisesRegex(ValueError,'fully opaque'):self.runcheck()

    def test_wrong_review_hash_file_and_missing_checks(self):
        original=copy.deepcopy(self.data)
        for mutation in ['sha','file','checks','observation','contradiction']:
            self.data=copy.deepcopy(original)
            if mutation=='sha':self.data['sha256']='0'*64
            if mutation=='file':self.data['file']=str(self.base/'other.png')
            if mutation=='checks':del self.data['checks']['materials']
            if mutation=='observation':self.data['checks']['form']['observation']='OK'
            if mutation=='contradiction':self.data['status']='pass';self.data['checks']['form']['status']='limited'
            self.review.write_text(json.dumps(self.data))
            with self.assertRaises(ValueError):self.runcheck()

    def test_call_only_receipt_not_artifact_binding(self):
        p=self.execution/'submission.json';r=json.loads(p.read_text());r['observedHandle']={'type':'imagegen-tool-call','id':'test'};p.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError,'artifact SHA'):self.runcheck()

    def test_null_reference_requires_no_facet_checks(self):
        s=dict(settingsVersion=3,topic='Phone',graphicType='icon',detailLevel='minimal',arrangement='auto',count=1,camera='front',creativity=3,whiteBase=False,background='transparent',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]),reference=None)
        self.execution=self.base/'null-reference'
        m=prepare(ROOT,dict(settings=s,prompt='A phone.'),self.execution)
        self.pin=m['manifestSha256'];self.bind()
        result=self.runcheck()
        self.assertTrue(result['evidenceValid'])
        self.assertEqual(result['reviewStatus'],'limited')
        self.assertFalse(result['artisticApproval'])
        self.assertIsNone(m['request']['settings']['reference'])
        self.assertEqual(set(self.data['checks']),CHECKS)

    def test_guided_result_requires_each_selected_facet_review(self):
        s=dict(settingsVersion=3,topic='Phone',graphicType='icon',detailLevel='minimal',arrangement='auto',count=1,camera='front',creativity=3,whiteBase=False,background='transparent',palette='natural',effects=[],recognizable=True,materials=dict(mode='auto',base=None,accents=[]),reference=dict(facets=['palette','materials']))
        self.execution=self.base/'guided'
        m=prepare(ROOT,dict(settings=s,prompt='A phone.',userReferences=[dict(path=str(ROOT/'assets/originals/coin.png'),role='GUIDANCE REFERENCE')]),self.execution)
        self.pin=m['manifestSha256'];self.bind()
        with self.assertRaisesRegex(ValueError,'Missing selected reference checks'):self.runcheck()
        for key in ('reference_palette','reference_materials'):
            self.data['checks'][key]=dict(status='limited',observation='Test fixture only: this comparison is not an artistic approval.')
        self.bind();self.assertEqual(self.runcheck()['reviewStatus'],'limited')

    def test_bad_filter_and_truncated_pixels(self):
        header=chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))
        for pixels in [bytes([5,20,40,60,255]),bytes([0,20])]:
            self.file.write_bytes(b'\x89PNG\r\n\x1a\n'+header+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))
            with self.assertRaises(ValueError):decode_png(self.file)

    def test_native_decode_keeps_strict_structure_checks(self):
        pixels=bytes([0,20,40,60,255])
        cases=[(8,3,0,chunk(b'PLTE',bytes([20,40,60])),zlib.compress(bytes([0,2]))),
               (8,6,0,b'',zlib.compress(pixels+pixels)),
               (8,6,0,b'',zlib.compress(pixels)+zlib.compress(pixels)),
               (8,6,2,b'',zlib.compress(pixels))]
        for depth,color,interlace,extra,compressed in cases:
            header=chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,depth,color,0,0,interlace))
            self.file.write_bytes(b'\x89PNG\r\n\x1a\n'+header+extra+chunk(b'IDAT',compressed)+chunk(b'IEND',b''))
            with self.assertRaises(ValueError): decode_png(self.file)

    def test_palette_transparency_and_16bit_alpha(self):
        for depth,color,pixels,extra in [(1,3,bytes([0,0]),chunk(b'PLTE',bytes([20,40,60]))+chunk(b'tRNS',bytes([0]))),(16,6,b'\0'+struct.pack('>HHHH',20,40,60,0),b''),(16,6,b'\0'+struct.pack('>HHHH',20,40,60,65534),b'')]:
            self.file.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,depth,color,0,0,0))+extra+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))
            self.assertEqual(decode_png(self.file)['nonopaquePixels'],1)

if __name__=='__main__':unittest.main()
