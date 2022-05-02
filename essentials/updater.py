#code repo: https://gist.github.com/bitmingw/69bfee10976a68078562a1f881eed5ab

from urllib.request import urlopen
from http.client import HTTPResponse
from subprocess import check_output
import json
import os
import sys

# Configurations
USERNAME = "Kinuseka"
REPO = "NHentaiAPI"
BRANCH = "master"
LOCAL_DIR = os.getcwd()


def github_sync(directory=LOCAL_DIR):
    os.chdir(directory)
    remote_sha = fetch_remove_sha()
    local_sha = fetch_local_sha()
    if remote_sha != local_sha:
        check_output(["git", "pull", "origin", BRANCH])
        print("The local repo has been updated")
        return 1
    else:
        print("The local repo is already up-to-date")
        return 0


def fetch_remove_sha():
    req_url = "https://api.github.com/repos/" + \
            USERNAME + "/" + REPO + "/branches/" + BRANCH
    resp = urlopen(req_url)
    resp_str = str(resp.read(), encoding="utf-8")
    resp_data = json.loads(resp_str)
    remote_sha = resp_data["commit"]["sha"]
    return remote_sha


def fetch_local_sha():
    check_output(["git", "checkout", BRANCH])
    local_sha = str(check_output(["git", "rev-parse", "HEAD"]), encoding="utf-8")
    return local_sha[:-1]  # remove newline


if __name__ == "__main__":
    sys.exit(github_sync(LOCAL_DIR))