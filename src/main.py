'''Mutating webhook to inject init or sidecar containers'''
import base64
import json
import logging
from copy import deepcopy
from os import getenv

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from jsonpatch import JsonPatch
from kubernetes import client

import setup

logging.basicConfig(
    level=getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI()
KUBE_API = client.CoreV1Api()


@app.get("/healthz")
def healthz():
    '''basic health endpoint for liveness'''
    return "OK"


@app.post("/mutate/pods")
async def mutating_webhook(request: Request):
    '''mutating webhook for modifying pods'''
    # get response body in array format
    body = await request.json()
    logging.debug("Request body:")
    logging.debug(body)

    # default response
    json_response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        'response': {
            'uid': body['request']['uid'],
            'allowed': True,
        }
    }

    original_pod = body['request']['object']
    namespace = body['request']['namespace']
    modified_pod = deepcopy(original_pod)

    print(body)

    pod_name = 'not_found'
    if 'name' in original_pod['metadata']:
        pod_name = original_pod['metadata']['name']
    if 'generateName' in original_pod['metadata']:
        pod_name = original_pod['metadata']['generateName']

    logging.info(
        f"Adding node selector and tolerations for pod {pod_name} project {namespace}")

    # Add project toleration
    if 'tolerations' not in modified_pod['spec']:
        modified_pod['spec']['tolerations'] = []
    project_toleration = {'key': 'project', 'operator': 'Equal',
                          'value': namespace}
    modified_pod['spec']['tolerations'].append(project_toleration)

    # add project nodeSelector
    if 'nodeSelector' not in modified_pod['spec']:
        modified_pod['spec']['nodeSelector'] = {}

    modified_pod['spec']['nodeSelector']['project'] = namespace

    # add patches if relevant
    patch = list(JsonPatch.from_diff(original_pod, modified_pod))
    if len(patch) > 0:
        logging.debug("Patches: %s:", patch)
        logging.debug("Pod after modification: %s", modified_pod)

        json_response['response']['patchType'] = 'JSONPatch'
        json_response['response']['patch'] = base64.b64encode(
            json.dumps(patch).encode("utf-8")).decode("utf-8")

        logging.debug("jsonResponse: %s", json_response)

    # return admissionreview json response
    return JSONResponse(content=jsonable_encoder(json_response))
