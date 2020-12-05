from os import path, scandir, remove
from datetime import datetime as dt
import simpleaudio as sa
import threading
from threading import RLock
from time import sleep

from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.utils import secure_filename
from flask import request, flash, current_app

ROOT = path.dirname(path.abspath(__name__)).split("api")[0]
print(ROOT)
DIR = path.join(ROOT, "media", "sounds")

App_ = current_app

playing = {}

def read_list():
    with  scandir(current_app.config.get('SOUND_DIR', DIR)) as entries:
        return [{"name":file.name,
                 "size": f"{file.stat().st_size/1024.:.2f} Kb",
                 "mdts": dt.isoformat(dt.fromtimestamp(file.stat().st_mtime))}
                for file in entries if file.is_file()]

def play(files=None, times=1, interval=1):
    s_dir = App_.config.get('SOUND_DIR', DIR)
    if not files:
        files = [path.join(s_dir, x.get('name')) for x in read_list() if x.get('name')]
    else:
        files = [path.join(s_dir, file.strip()) for file in files.split(",")]
        wrong = [file for file in files if not path.isfile(file)]
        if wrong:
            return f'Not found: {",".join((path.split(x)[1] for x in wrong))}', 404

    with RLock():
        for f in files:
            if f in playing.keys():
                playing[f].stop()
                return f"Stop Playing {', '.join((path.split(x)[1] for x in files))}", 200

    play_sound = Play(files = files, times=times, interval=interval)
    play_sound.start()
    return f"Playing {', '.join((path.split(x)[1] for x in files))}", 200

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ('wav', 'mp3')

def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return 'No file spec', 400
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return 'No file name', 422 #redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(path.join(App_.config.get('SOUND_DIR', DIR), filename))
            return 'OK', 201
    return 'Only sound accepted', 422

def delete_file(file=None):
    if not file or file not in (x.get('name') for x in read_list()):
        return "Bad request", 400
    file = path.join(App_.config.get('SOUND_DIR', DIR), file)
    try:
        remove(file)
    except OSError as e:
        print(e)
        return "Internal Server Error", 500
    return "Deleted", 204

class Play(threading.Thread):
    def __init__(self, files=None, times=1, interval=1, **kwargs):
        super().__init__(**kwargs)
        self.files = files or []
        self.times = times
        self.interval = interval
        self.daemon = False

    def run(self):
        for n in range(len(self.files)):
            with RLock():
                playing[self.files[n]] = self
            for i in range(self.times):
                wave_obj = sa.WaveObject.from_wave_file(self.files[n])
                self.play_obj = wave_obj.play()
                self.play_obj.wait_done()
                if n < len(self.files) and i < self.times:
                    sleep(self.interval)
            with RLock():
                try:
                    del playing[self.files[n]]
                except:
                    pass

    def stop(self):
        sa.stop_all()


if __name__ == '__main__':
    print(read_list())
    for i in read_list():
        print(i)
    pl = Play(files=read_list())
    pl.start()