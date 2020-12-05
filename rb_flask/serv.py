from flask import render_template, Flask, logging
import connexion
from os import path, urandom
import logging
logger = logging.getLogger("serv")

ROOT_DIR = path.dirname(path.abspath(__name__)).split("api")[0]
SOUND_DIR = path.join(ROOT_DIR, "media", "sounds")

logger.error(f"ROOT_DIR : {ROOT_DIR}")

App = connexion.App(__name__,
specification_dir="./",
                    )

App.add_api('api/v1/swagger.yaml')
App.app.config.from_mapping(SOUND_DIR=SOUND_DIR)
App.app.secret_key = urandom(32)



from os import scandir
from datetime import datetime as dt
def read_list():
    with  scandir(App.app.config.get('SOUND_DIR')) as entries:
        return [{"name":file.name,
                 "size": f"{file.stat().st_size/1024.:.2f} Kb",
                 "mdts": dt.isoformat(dt.fromtimestamp(file.stat().st_mtime))}
                for file in entries if file.is_file()]

@App.route("/")
def index():
    return render_template("home.html", files=read_list())


def register_specs(cxn):
    """ Register Connexion APIs.
    """
    api_options = {
        'swagger_ui': cxn.app.config.get('SWAGGER_UI_ENABLED')
    }

    cxn.add_api('v1/swagger.yaml', strict_validation=True, options=api_options)

if __name__ == "__main__":
    App.run(port=80, debug=True)