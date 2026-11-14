"""Synthetic engineering fixtures only; these are NOT NASA medical documents."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
from contextlib import closing
import sqlite3
import struct
import tempfile
import unittest
import zlib

SOURCE = Path(__file__).resolve().parents[1] / "scripts/audit_cliff119_library.py"
spec = importlib.util.spec_from_file_location("cliff119_release_audit", SOURCE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def png(rgb):
    def chunk(tag, b):
        return struct.pack(">I",len(b)) + tag + b + struct.pack(">I", zlib.crc32(tag+b) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR",struct.pack(">2I5B",1,1,8,2,0,0,0)) + chunk(b"IDAT",zlib.compress(bytes([0])+bytes(rgb)))+chunk(b"IEND",b"")


class ReleaseAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "library.sqlite"
        self.manifest_path = self.root / "manifest.json"
        self.catalog_path = self.root / "catalog.json"

    def build_fixture(self):
        # Fake NASA URLs are quarantined in tempfile; tests only verify validator behavior.
        # Never import this fixture into a real AETHERION library or claim as NASA evidence.
        db = sqlite3.connect(self.db_path)
        db.execute("PRAGMA foreign_keys=ON")
        schema_file = Path(__file__).resolve().parents[1] / "knowledge/nasa/cliff_119_2023/library_schema.py"
        # Inline the schema source via module loading so test stays compatible with repository.
        s = importlib.util.spec_from_file_location("libschema_test", schema_file)
        schema = importlib.util.module_from_spec(s)
        s.loader.exec_module(schema)
        schema.initialize(db)
        files=[]
        entries=[]
        for i in range(1, 120):
            title=f"SYNTHETIC TEST ONLY {i}"
            ident=f"CLIFF-{i:03d}"
            sid=f"synthetic-{i:03d}"
            url=f"https://www.nasa.gov/SYNTHETIC-TEST-ONLY-{i}.pdf"
            data=f"%PDF-1.4\nNOT A REAL NASA PDF {i}\n%%EOF".encode()
            sha=hashlib.sha256(data).hexdigest()
            p=self.root/"original"/f"fake-{i:03d}.pdf"
            p.parent.mkdir(exist_ok=True)
            p.write_bytes(data)
            files.append({"status":"downloaded","source_url":url,"sha256":sha,"path":f"original/{p.name}","bytes":len(data)})
            entries.append({"slot":i,"article_id":ident,"source_title":title,"original_document_url":url,"url_verification":"VERIFIED"})
            db.execute("INSERT INTO sources(source_id,publisher,title,source_url,content_sha256,original_bytes,license_identifier,attribution,verification_state,retrieved_at_utc) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (sid,"NASA",title,url,sha,len(data),"US_GOV_PUBLIC_DOMAIN","SYNTHETIC test publisher","VERIFIED","2026-11-14T00:00:00+00:00"))
            db.execute("INSERT INTO articles(article_id,slot,display_title,category,source_id,completeness_state,created_utc,updated_utc) VALUES(?,?,?,?,?,'COMPLETE','2026','2026')",
                (ident,i,title,"SYNTHETIC",sid))
            db.execute("INSERT INTO article_sections(section_id,article_id,ordinal,heading,text_content,page_start) VALUES(?,?,0,'TEST','Synthetic content, not medical advice',1)", (f"s{i}",ident))
            db.execute("INSERT INTO source_references(reference_id,article_id,ordinal,label,citation_url) VALUES(?,?,0,'TEST',?)",(f"r{i}",ident,url))
            for j, rgb in enumerate(((255,0,0),(0,255,0),(0,0,255))):
                b=png(rgb); digest=hashlib.sha256(b).hexdigest()
                db.execute("INSERT INTO media(media_id,article_id,ordinal,media_kind,data,mime_type,sha256,creator,license_identifier,source_url,attribution,caption,alt_text,usage_review) VALUES(?,?,?,'DIAGRAM',?,'image/png',?,'TEST','CC0-1.0',?,'TEST','Synthetic test figure','Synthetic test alt','APPROVED')",
                    (f"m{i}-{j}",ident,j,b,digest,url))
        db.commit()
        db.close()
        self.manifest_path.write_text(json.dumps({"files":files,"complete":True,"downloaded_pdf_count":119}),encoding="utf-8")
        self.catalog_path.write_text(json.dumps({"entries":entries}),encoding="utf-8")
        return entries,files

    def run_audit(self):
        return audit.audit_library(self.db_path,self.catalog_path,self.manifest_path)

    def codes(self):
        return {e['code'] for e in self.run_audit()['issues']}

    def test_missing_db_manifest_and_unresolved_source_block_release(self):
        report=self.run_audit()
        self.assertFalse(report['passed'])
        self.assertTrue({'DATABASE_MISSING','MANIFEST_MISSING','CATALOG_MISSING'} <= {x['code'] for x in report['issues']})

    def test_synthetic_full_fixture_tests_auditor_logic_only(self):
        self.build_fixture()
        report=self.run_audit()
        self.assertTrue(report['passed'], report['issues'][:5])
        self.assertEqual(report['counts']['articles'],119)
        self.assertEqual(report['counts']['verified_originals'],119)
        self.assertEqual(report['counts']['verified_images'],357)

    def test_tampered_source_document_blocks_release(self):
        self.build_fixture()
        (self.root/'original/fake-001.pdf').write_bytes(b'tampered')
        self.assertIn('ORIGINAL_HASH_MISMATCH',self.codes())

    def test_unresolved_119th_link_blocks_release(self):
        self.build_fixture()
        v=json.loads(self.catalog_path.read_text())
        v['entries'][-1]['original_document_url']=None
        self.catalog_path.write_text(json.dumps(v))
        self.assertIn('DIRECT_URL_UNVERIFIED',self.codes())

    def test_corrupt_image_and_unlicensed_image_block_release(self):
        self.build_fixture()
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("UPDATE media SET data=?,license_identifier='UNKNOWN' WHERE media_id='m1-0'",(b'not png',))
        self.assertIn('IMAGE_CORRUPT',self.codes())
        self.assertIn('IMAGE_COVERAGE',self.codes())

    def test_missing_article_and_source_citation_block_release(self):
        self.build_fixture()
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("DELETE FROM articles WHERE slot=119")
            db.execute("DELETE FROM source_references WHERE article_id='CLIFF-001'")
        codes=self.codes()
        self.assertTrue({'ARTICLE_COUNT','ARTICLE_MISSING','CITATIONS_MISSING'} <= codes)

    def test_duplicate_direct_source_is_rejected(self):
        self.build_fixture()
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("UPDATE sources SET source_url='https://www.nasa.gov/SYNTHETIC-TEST-ONLY-1.pdf' WHERE source_id='synthetic-002'")
        self.assertIn('DUPLICATE_SOURCE_URL',self.codes())

    def test_malicious_domain_not_nasa(self):
        for bad in ['https://nasa.gov.evil.test/file.pdf','https://evilnasa.gov/file.pdf','http://www.nasa.gov/file.pdf']:
            self.assertFalse(audit.nasa_url(bad))
        self.assertTrue(audit.nasa_url('https://www.nasa.gov/file.pdf'))


if __name__ == '__main__':
    unittest.main()
