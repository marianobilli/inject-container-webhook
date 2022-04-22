'''Mutating webhook to inject init or sidecar containers'''
import base64
import json
import logging
from copy import deepcopy
from os import getenv

import yaml
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from jsonpatch import JsonPatch

logging.basicConfig(
    level=getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI()

try:
    init_containers = yaml.safe_load(
        open("config/initcontainers.yaml", "r", encoding="UTF-8"))
except FileNotFoundError:
    init_containers = []

try:
    sidecar_containers = yaml.safe_load(
        open("config/sidecarcontainers.yaml", "r", encoding="UTF-8"))
except FileNotFoundError:
    sidecar_containers = []


@app.get("/healthz")
def healthz():
    '''basic health endpoint for liveness'''
    return "OK"


def add_containers_to_spec(containers: list, key: str, pod_spec: dict):
    '''Adds a given list of containers to the pod spec'''
    if len(containers) > 0:
        if key in pod_spec:
            for container in containers:
                pod_spec[key].insert(
                    0, container)
        else:
            pod_spec[key] = containers


@app.post("/mutate/pods")
async def mutating_webhook(request: Request):
    '''mutating webhook for modifying pods'''
    # get response body in array format
    body = await request.json()
    logging.info("Request body:")
    logging.info(body)

    original_pod = body['request']['object']
    modified_pod = deepcopy(original_pod)

    add_containers_to_spec(
        init_containers, 'initContainers', modified_pod['spec'])
    add_containers_to_spec(
        sidecar_containers, 'containers', modified_pod['spec'])

    # default response
    json_response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        'response': {
            'uid': body['request']['uid'],
            'allowed': True,
        }
    }

    # add patches if relevant
    patch = list(JsonPatch.from_diff(original_pod, modified_pod))
    if len(patch) > 0:
        logging.info("Patches: %s:", patch)
        logging.debug("Pod after modification: %s", modified_pod)

        json_response['response']['patchType'] = 'JSONPatch'
        json_response['response']['patch'] = base64.b64encode(
            json.dumps(patch).encode("utf-8")).decode("utf-8")

        logging.debug("jsonResponse: %s", json_response)

    # return admissionreview json response
    return JSONResponse(content=jsonable_encoder(json_response))
