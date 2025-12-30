#!/usr/bin/env python3

import http.client
import httplib2
import json
import logging
import atexit
from sys import argv, exit
from os import path
from time import sleep
from random import random
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow, flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow



# Explicitly tell the underlying HTTP transport library not to retry, since we are handling retry logic ourselves.
httplib2.RETRIES = 1

UPLOAD_CHUNKSIZE = 1024 * 1024 # (1 MB)
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS: tuple = (
    httplib2.HttpLib2Error, IOError, http.client.NotConnected,
    http.client.IncompleteRead, http.client.ImproperConnectionState,
    http.client.CannotSendRequest, http.client.CannotSendHeader,
    http.client.ResponseNotReady, http.client.BadStatusLine
)
RETRIABLE_STATUS_CODES: list[int] = [500, 502, 503, 504]
LOG_FILE: str = path.realpath(path.join(path.dirname(__file__), "../uploads.log"))
PROGRESS_FILE: str = path.realpath(path.join(path.dirname(__file__), "../progress.json"))
CLIENT_SECRETS_FILE: str = path.realpath(path.join(path.dirname(__file__), "client_secrets.json"))
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MISSING_CLIENT_SECRETS_MESSAGE: str = f"""
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

  {path.abspath(path.join(path.dirname(__file__), CLIENT_SECRETS_FILE))}

with information from the API Console
https://console.cloud.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
"""
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")
logging.basicConfig(
    level=logging.CRITICAL,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]:  %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    encoding="utf-8",
    filename=LOG_FILE,
    filemode="a"
)



def remove_progress_info() -> None:
    if not path.exists(PROGRESS_FILE):
        return
    
    with open(PROGRESS_FILE, "r") as file:
        upload_progress: dict = json.load(file)
    if task_name in upload_progress:
        del upload_progress[task_name]
        with open(PROGRESS_FILE, "w") as file:
            json.dump(upload_progress, file, indent=2)


def get_authenticated_service(args) -> Resource:
    flow: OAuth2WebServerFlow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_UPLOAD_SCOPE, message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage: Storage = Storage(f"{argv[0]}-oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=credentials.authorize(httplib2.Http()))


def update_progress(progress: float) -> None:
    if not path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "w") as file:
            json.dump({}, file)

    with open(PROGRESS_FILE, "r") as file:
        upload_status: dict = json.load(file)

    upload_status[task_name] = f"{(progress * 100):.2f}%"

    with open(PROGRESS_FILE, "w") as file:
        json.dump(upload_status, file, indent=2)


def initialize_upload(youtube, options) -> None:
    tags = None
    if options.keywords:
        tags = options.keywords.split(",")

    body: dict = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    # create and upload the video
    insert_request = youtube.videos().insert(
        part=",".join(list(body.keys())),
        body=body,
        media_body=MediaFileUpload(options.file, chunksize=UPLOAD_CHUNKSIZE, resumable=True)
    )
    logger.info("Starting upload...")
    update_progress(0.0)
    resumable_upload(insert_request)


def resumable_upload(insert_request) -> None:
    response = None
    error: str | None = None
    retry: int = 0
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if status is not None:
                update_progress(status.progress())

            if response is not None:
                if 'id' in response:
                    logger.info(f"Video ID '{response['id']}' successfully uploaded.")
                else:
                    logger.critical(f"Upload failed with an unexpected response: {response}")
                    exit(1)
        except HttpError as ex:
            if ex.resp.status in RETRIABLE_STATUS_CODES:
                error = f"A retriable HTTP error {ex.resp.status} occurred:\n{ex.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as ex:
            error = f"A retriable error occurred: {type(ex).__name__}: {ex}"

        if error is not None:
            logging.debug(error)
            retry += 1
            if retry > MAX_RETRIES:
                logger.critical("Upload failed (too many interruptions).")
                exit(1)

            max_sleep: int = 2 ** retry
            sleep_seconds: int = int(random() * max_sleep)
            logger.debug(f"Sleeping {sleep_seconds} seconds and then retrying...")
            sleep(sleep_seconds)


if __name__ == '__main__':
    argparser.add_argument("--file", required=True, help="Video file to upload") # type: ignore
    argparser.add_argument("--title", help="Video title", default="[Insert Title]") # type: ignore
    argparser.add_argument("--description", help="Video description", default="[Insert Description]") # type: ignore
    argparser.add_argument("--category", default="20", # (Gaming) # type: ignore
                           help="Numeric video category. See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", help="Video keywords, comma separated", default="") # type: ignore
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES, default="private", # type: ignore
                           help="Video privacy status.")
    args = argparser.parse_args() # type: ignore

    task_name: str = path.basename(args.file)
    logger: logging.Logger = logging.getLogger(task_name)
    logger.setLevel(logging.INFO)

    atexit.register(remove_progress_info)

    if not path.exists(args.file):
        logger.critical(f"Invalid file path ({args.file}).")
        exit(1)

    youtube: Resource = get_authenticated_service(args)
    try:
        initialize_upload(youtube, args)
    except HttpError as e:
        logger.critical(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        exit(1)
