import os
import time
import requests
import logging
import json
from dotenv import load_dotenv
from luci_exception import LuciException


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)s]   %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_rpc_error(error):
    if error is not None:
        msg = f"Got RCP error {error}"
        logger.critical(msg)
        raise LuciException(msg)


def get_new_token(url: str, username: str, password: str) -> str:
    body = {
        "id": 1,
        "method": "login",
        "params": [username, password]
    }

    payload = json.dumps(body)

    res = requests.post(url, data=payload, timeout=4)

    if not res.ok:
        msg = f"Got unexpected response code {res.status_code}"
        logger.critical(msg)
        raise LuciException(msg)

    check_rpc_error(res.json()['error'])

    token = res.json()['result']
    if token is None:
        msg = f"Authentication failed"
        logger.critical(msg)
        raise LuciException(msg)

    return token


def set_iface(url: str, if_name: str, if_status: str, token: str):

    if if_status not in ['0', '1']:
        msg = f"Interface status should be 0 or 1, got {if_status}. Aborting..."
        logger.critical(msg)
        raise LuciException(msg)

    body_set = {
        "method": "set",
        "params": ["network", if_name, "auto", if_status]
    }

    set_payload = json.dumps(body_set)

    body_commit = {
        "method": "commit",
        "params": ["network"]
    }

    commit_payload = json.dumps(body_commit)

    params = {"auth": token}

    res = requests.post(url, params=params, data=set_payload)

    if not res.ok:
        msg = f"Failed to set interface {if_name} to {if_status} with the error code {res.status_code}"
        logger.critical(msg)
        raise LuciException(msg)

    check_rpc_error(res.json()['error'])

    res = requests.post(url, params=params, data=commit_payload)

    if not res.ok:
        msg = f"Failed to commit changes with the error code {res.status_code}"
        logger.critical(msg)
        raise LuciException(msg)

    check_rpc_error(res.json()['error'])


def get_iface(url: str, if_name: str, token: str) -> str:

    body = {
        "method": "get_all",
        "params": ["network", if_name]
    }

    payload = json.dumps(body)

    params = {"auth": token}

    res = requests.post(url, params=params, data=payload)

    if not res.ok:
        msg = f"Failed to get interface status for {if_name}"
        logger.warn(msg)

    check_rpc_error(res.json()['error'])

    return res.json()['result']


def main():

    load_dotenv()

    username = os.environ.get("LuCI_USER")
    password = os.environ.get("LuCI_PASS")
    rpc_host = os.environ.get("LuCI_HOST")

    if not all([username, password, rpc_host]):
        msg = f"Failed to parse ENV data. Please specify LuCI username, password and host"
        logger.critical(msg)
        exit(1)

    auth_url = rpc_host + '/auth'
    uci_url = rpc_host + '/uci'

    logger.info("Authenticating...")
    token = get_new_token(auth_url, username, password)

    if_name = 'lte'
    if_state = '1'

    logger.info(f"Setting interface {if_name} to {if_state}")
    set_iface(uci_url, if_name, if_state, token)

    logger.info(f"Verifying current state for {if_name}")
    time.sleep(2)
    iface_data = get_iface(uci_url, if_name, token)
    logger.info(f"Current interface state: {iface_data}")


if __name__ == '__main__':
    try:
        main()
    except LuciException as e:
        print(e)
    except requests.exceptions.ConnectTimeout:
        print("Connection timed out. Check if the remote host is alive")
    except requests.exceptions.ReadTimeout:
        print("Reading from a connection timed out. Remote host is too slow?")

