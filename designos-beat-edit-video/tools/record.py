"""Record one owned take; never infer ownership from global modification times."""
import argparse, json, os, shutil, subprocess
from pathlib import Path


def executable():
    configured = os.environ.get('OPENSCREEN')
    candidates = [configured] if configured else [shutil.which('openscreen'), '/Applications/Openscreen.app/Contents/MacOS/Openscreen', str(Path.home() / 'Applications/Openscreen.app/Contents/MacOS/Openscreen')]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError('Install Openscreen or set OPENSCREEN to its executable path')


def record(out, name, seconds):
    if not name or Path(name).name != name or name in ('.', '..'):
        raise ValueError('take_name must be a single filename')
    if seconds <= 0:
        raise ValueError('duration must be positive')
    out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    lock = out / (name + '.lock')
    # Exclusive reservation protects same-name recordings across processes.
    with lock.open('x'):
        pass
    try:
        project = out / (name + '.openscreen')
        targets = [project, out/(name+'.log'), out/(name+'.mp4'), out/(name+'.cursor.json')]
        if any(p.exists() for p in targets):
            raise FileExistsError('Take already exists; choose a new name')
        with targets[1].open('x') as log:
            subprocess.run([executable(), 'record', '--window', 'design:os studio', '--cursor', 'editable-overlay', '--duration', str(seconds), '--project', str(project), '--json'], stdout=log, stderr=subprocess.STDOUT, check=True)
        events = []
        for line in targets[1].read_text().splitlines():
            try: events.append(json.loads(line))
            except json.JSONDecodeError: pass
        done = [e for e in events if e.get('event') == 'done' and e.get('success') is True]
        if len(done) != 1 or any(e.get('event') == 'warning' for e in events):
            raise RuntimeError('Recording incomplete; inspect take log. No media copied.')
        event = done[0]
        if event.get('warnings'):
            raise RuntimeError('Recording reported warnings; inspect log')
        data = json.loads(project.read_text())
        source = Path(data['media']['screenVideoPath']).expanduser()
        if not source.is_absolute(): source = project.parent / source
        source = source.resolve()
        reported = Path(event['screenVideoPath']).expanduser().resolve()
        if source != reported:
            raise RuntimeError('Project and completion event disagree about take')
        cursor = Path(event.get('cursorDataPath', str(source)+'.cursor.json'))
        if not source.is_file() or not cursor.is_file():
            raise RuntimeError('Owned video or cursor file missing')
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(source)]))
        if float(probe['format']['duration']) <= 0: raise RuntimeError('Empty recording')
        shutil.copyfile(source, targets[2]); shutil.copyfile(cursor, targets[3])
        print(json.dumps({'video':str(targets[2]),'cursor':str(targets[3]),'source':str(source)}))
    finally:
        lock.unlink()


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('out_dir'); p.add_argument('take_name'); p.add_argument('seconds',nargs='?',type=float,default=30)
    a=p.parse_args(); record(a.out_dir,a.take_name,a.seconds)
