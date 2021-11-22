from flask import Flask
from sqlalchemy import create_engine
from babbage.manager import JSONCubeManager
from babbage.api import configure_api
from pipeline import (update_fiscal_schema, cloud_storage, 
                      runpipeline_subcommand, generate_org )
import logging
import requests
import os

log = logging.getLogger(__name__)

app = Flask(__name__)
engine = create_engine('postgresql://steveoni@localhost/testing')
models_directory = 'models/'
manager = JSONCubeManager(engine, models_directory)
blueprint = configure_api(app, manager)
app.register_blueprint(blueprint, url_prefix='/api/babbage/')

@app.route('/api/pipeline/<org>')
def pipeline(org):
    """
    API call to start the pipeline
    for creating gift-api 
    """
    print("START API PIPELINE")
    github_dpkg = f'https://raw.githubusercontent.com/gift-data/{org}/main/datapackage.json'
    dpkg = requests.get(github_dpkg).json()

    # check if organisation folder already exist
    if (not os.path.isdir(org)):
        generate_org(org, dpkg)

    # update fiscal YAML file
    update_fiscal_schema(org)

    # download resources from google cloud
    print("Downloading resources from Google bucket")
    cloud_storage(dpkg, org)

    # run datapackage-pipeline command line
    print("START PIPELINE SUBCOMMAND")
    runpipeline_subcommand(org)

    return "done"


app.run(host="localhost", port=3000, debug=True)
