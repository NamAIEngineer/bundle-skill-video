import importlib.util, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]/'designos-beat-edit-video'
spec=importlib.util.spec_from_file_location('recorder',ROOT/'tools/record.py');rec=importlib.util.module_from_spec(spec);spec.loader.exec_module(rec)

class RecordingTests(unittest.TestCase):
    def test_ownership_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=root/'owned.mp4';source.write_bytes(b'owned');cursor=root/'owned.mp4.cursor.json';cursor.write_text('{}')
            (root/'newest-unrelated.mp4').write_bytes(b'wrong')
            def run(argv,stdout,**kwargs):
                project=Path(argv[argv.index('--project')+1]);project.write_text(json.dumps({'media':{'screenVideoPath':str(source)}}))
                stdout.write(json.dumps({'event':'done','success':True,'screenVideoPath':str(source),'cursorDataPath':str(cursor)})+'\n')
            with patch.object(rec,'executable',return_value='openscreen'),patch.object(rec.subprocess,'run',side_effect=run),patch.object(rec.subprocess,'check_output',return_value=b'{"format":{"duration":"1"}}'):
                rec.record(root/'takes','one',1)
                self.assertEqual((root/'takes/one.mp4').read_bytes(),b'owned')
                with self.assertRaises(FileExistsError):rec.record(root/'takes','one',1)
            self.assertFalse((root/'takes/one.lock').exists())
    def test_lock_and_invalid_names(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'one.lock').touch()
            with self.assertRaises(FileExistsError):rec.record(d,'one',1)
            self.assertTrue((Path(d)/'one.lock').exists())
            with self.assertRaises(ValueError):rec.record(d,'../escape',1)
    def test_failure_does_not_copy(self):
        with tempfile.TemporaryDirectory() as d:
            def run(argv,stdout,**kwargs):stdout.write('{"event":"done","success":false}\n')
            with patch.object(rec,'executable',return_value='openscreen'),patch.object(rec.subprocess,'run',side_effect=run):
                with self.assertRaises(RuntimeError):rec.record(d,'bad',1)
            self.assertFalse((Path(d)/'bad.mp4').exists())

class TimingTests(unittest.TestCase):
    def test_generated_bar_and_typing_grid(self):
        import sys
        sys.path.insert(0,str(ROOT/'engine'))
        import ideate, beatlib
        p=ideate.plan({'seed':17,'edits':5})
        for e in p['edits']:
            self.assertAlmostEqual(e['T']/(240/p['bpm']),e['bar'],places=10)
        c={'name':'x','scene':'x','T':p['edits'][0]['T'],'tc':0,'hit':0.5,'td':1,'ts':2,'te':3,'N':2,'new':'ok','row':0.2,'pt':[0.5,0.5]}
        tl=beatlib.Timeline({'fps':30,'bpm':p['bpm'],'total':20,'scenes':[['x',0,20,1]],'cards':[c]})
        self.assertFalse(tl.validate())

if __name__=='__main__': unittest.main()
