#!/usr/bin/env python
import re
import argparse
import subprocess
import logging
import json
import socket
import tempfile
import sys
import zipfile
import ssl

try:
    import urllib.request as urlrequest
except ImportError:
    import urllib2 as urlrequest

import time
import os
import shutil
import hashlib
from datetime import datetime, timedelta
from operator import itemgetter

DEFAULT_SSH_KEY_NAME = os.path.join(tempfile.gettempdir(), "upgrade_ssh_key")

UPGRADE_SERVER_NAME = os.environ.get("UPGRADE_SERVER_NAME", "https://upgrade.odoo.com")
DATA_SERVER_NAME = os.environ.get("DATA_SERVER_NAME", "upgrade.odoo.com")
DATA_SERVER_USER = "odoo"
DATA_SERVER_PATH = "/data"
SSH_KEY_NAME = os.environ.get("SSH_KEY_NAME", DEFAULT_SSH_KEY_NAME)
SSL_VERIFICATION = os.environ.get("SSL_VERIFICATION", "1").strip().lower() not in {
    "0",
    "off",
    "no",
}

ORIGIN_DUMP_BASE_NAME = "origin"
ORIGIN_DUMP_NAME = "origin.dump"
EXPECTED_DUMP_EXTENSIONS = [".sql", ".dump", ".zip", ".sql.gz"]
POSTGRES_TABLE_OF_CONTENTS = "toc.dat"
FILESTORE_NAME = "filestore"
FILESTORE_PATH = os.path.expanduser("~/.local/share/Odoo/filestore")

DB_TIMESTAMP_FORMAT = "%Y_%m_%d_%H_%M"

REQUEST_TIMEOUT = 60
STATUS_MONITORING_PERIOD = 5
LOG_REFRESH_PERIOD = 5
CORE_COUNT = 4

ssl_context = (
    ssl.create_default_context()
    if SSL_VERIFICATION
    else ssl._create_unverified_context()
)


class UpgradeError(Exception):
    """Generic exception to handled any kind of upgrade errors in a same way"""

    pass


class StateMachine:
    """
    Simple state machine with states and handlers.
    * A state machine has a specific context (internal data) which may be updated with `update_context`.
    Each handler may access to the context using the `get_context_data` method.
    * States are defined using the `set_states` method, with a name and a handler.
    * A handler executes all the processing for a specific state and returns the next state to execute or None if
    it's a terminal state.
    * The `run` method starts the state machine execution from a specific state with an optional additional context,
    until a terminal state.
    """

    class Error(Exception):
        pass

    def __init__(self):
        self.handlers = {}
        self.current_state = None
        self.context = {}

    def update_context(self, data):
        self.context.update(data)

    def get_context_data(self, keys):
        """
        check if all `keys` identify a data in the FSM context and return them
        """
        if any(k not in self.context for k in keys):
            raise StateMachine.Error(
                "The following data are missing for the state '%s': %s"
                % (
                    self.current_state,
                    ", ".join([k for k in keys if k not in self.context]),
                )
            )

        return itemgetter(*keys)(self.context)

    def set_states(self, handlers):
        """
        Define the states of the state machine
        Each `handler` shall return the next state.
        """
        self.handlers = handlers

    def run(self, from_state, additional_context=None):
        """
        Execute the state machine from `from_state` with an optional additional context.
        If an additional context is specified, the current context will be updated.
        """
        if from_state not in self.handlers:
            raise StateMachine.Error(
                "The state '%s' is not a valid state." % from_state
            )

        if additional_context is not None:
            self.context.update(additional_context)

        self.current_state = from_state

        while self.current_state is not None:
            handler = self.handlers[self.current_state]
            self.current_state = handler(self)


# ---------------------------------------------------------------------------------
# Common functions
# ---------------------------------------------------------------------------------


def user_confirm():
    return sys.stdin.read(1) not in ("n", "N")


def run_command(command, stream_output=False):
    """
    Run a Linux command.
    Here, check_output is used to retrieve the command output when
    an exception is raised.
    """
    try:
        if stream_output:
            subprocess.check_call(command, stderr=subprocess.STDOUT)
        else:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
        return
    except subprocess.CalledProcessError as e:
        error_msg = "The '%s' command has failed" % e.cmd[0]
        if not stream_output:
            error_msg += " with the following output:\n %s" % e.output.decode(
                "utf-8"
            ).rstrip("\n")
    raise UpgradeError(error_msg)


# This is an advanced version of os.path.basename in python 2, which can get both dir and file basename from path
def get_path_basename(path):
    return os.path.basename(path if not path.endswith(os.sep) else path[:-1])


def get_path_nth_parent(path, n=1):
    return os.path.abspath(path + n * "/..")


# ---------------------------------------------------------------------------------
# Data transfer functions
# ---------------------------------------------------------------------------------


def clean_default_ssh_keys():
    if os.path.isfile(DEFAULT_SSH_KEY_NAME):
        os.remove(DEFAULT_SSH_KEY_NAME)

    if os.path.isfile(DEFAULT_SSH_KEY_NAME + ".pub"):
        os.remove(DEFAULT_SSH_KEY_NAME + ".pub")


def generate_default_ssh_keys():
    """
    Generate public/private SSH key pair in the current working directory
    """
    if not os.path.isfile(DEFAULT_SSH_KEY_NAME) or not os.path.isfile(
        "%s.pub" % DEFAULT_SSH_KEY_NAME
    ):
        logging.info("Generating temporary public/private SSH key pair")
        clean_default_ssh_keys()
        run_command(["ssh-keygen", "-t", "rsa", "-N", "", "-f", DEFAULT_SSH_KEY_NAME])


def upload_dump(dump_path, server, port, user, path, ssh_key, dest_dump_name=None):
    """
    Upload the database dump to the server through SSH.
    """
    server_string = "%s@%s:%s" % (
        user,
        server,
        "%s/%s" % (path, dest_dump_name) if dest_dump_name else path,
    )
    # if the --dump dir is passed, then transfer only the content of the dir, and not the directory itself
    if os.path.isdir(dump_path) and not dump_path.endswith(os.sep):
        dump_path += os.sep

    logging.info("Upload the database dump.")
    try:
        run_command(
            [
                "rsync",
                "--chmod=u+rwx,g+rwx,o+r",
                "--info=progress2",
                "-are",
                "ssh -p %s -o IdentitiesOnly=yes -i %s" % (port, ssh_key),
                dump_path,
                server_string,
            ],
            stream_output=True,
        )
    except Exception:
        logging.error(
            "The connection may have been been closed because you reached the 5 minutes timeout. Please, re-run the script and resume."
        )
        raise


def download_dump(
    server, port, user, dump_path, dump_name, ssh_key, dump_dest_path="."
):
    """
    Download a database dump and its filestore from the server through SSH
    """
    ssh = "ssh -p %s -o IdentitiesOnly=yes -i %s" % (port, ssh_key)
    server = "%s@%s:%s" % (user, server, dump_path)
    server_dump_path = os.path.join(server, dump_name)
    server_fs_path = os.path.join(server, FILESTORE_NAME)
    reports_path = os.path.join(server, "upgrade-report.html")
    logs_path = os.path.join(server, "upgrade.log")

    logging.info(
        "Downloading the database dump and its filestore from %s.",
        server,
    )
    try:
        run_command(
            [
                "rsync",
                "--info=progress2",
                "-are",
                ssh,
                "--ignore-missing-args",
                server_dump_path,
                server_fs_path,
                reports_path,
                logs_path,
                dump_dest_path,
            ],
            stream_output=True,
        )
    except Exception:
        logging.error(
            "The connection may have been been closed because you reached the 5 minutes timeout. Please, re-run the script and resume."
        )
        raise


# ---------------------------------------------------------------------------------
# DB management functions
# ---------------------------------------------------------------------------------


def get_dump_name(dbname):
    return ORIGIN_DUMP_NAME


def get_upgraded_db_name(dbname, target, aim):
    timestamp = datetime.now().strftime(DB_TIMESTAMP_FORMAT)

    if aim == "production":
        return "%s_backup_%s" % (dbname, timestamp)

    return "%s_test_%s_%s" % (dbname, target, timestamp)


def dump_database(db_name, dump_name, core_count):
    """
    Dump the database as dump_name using 'core_count' CPU to reduce the dumping time.
    """
    logging.info("Dump the database '%s' as '%s'", db_name, dump_name)

    clean_dump(dump_name)

    run_command(
        [
            "pg_dump",
            "--no-owner",
            "--format",
            "d",
            "--jobs",
            str(core_count),
            "--file",
            dump_name,
            db_name,
        ]
    )

# pg_restore --no-owner --format d upgraded.dump --dbname dp_test --jobs 15
def restore_database(db_name, dump_name, core_count):
    """
    Restore the upgraded database locally using 'core_count' CPU to reduce the restoring time.
    """
    logging.info("Restore the dump file '%s' as the database '%s'", dump_name, db_name)

    run_command(["createdb", db_name])
    run_command(
        [
            "pg_restore",
            "--no-owner",
            "--format",
            "d",
            dump_name,
            "--dbname",
            db_name,
            "--jobs",
            str(core_count),
        ]
    )


def restore_filestore(origin_db_name, upgraded_db_name):
    """
    Restore the new filestore by merging it with the old one, in a folder named
    as the upgraded database.
    If the previous filestore is not found, the new filestore should be restored manually.
    """
    origin_fs_path = os.path.join(FILESTORE_PATH, origin_db_name)

    if os.path.exists(origin_fs_path):
        new_fs_path = os.path.join(FILESTORE_PATH, upgraded_db_name)

        logging.info(
            "Merging the new filestore with the old one in %s ...", new_fs_path
        )
        shutil.copytree(origin_fs_path, new_fs_path)
        run_command(["rsync", "-a", FILESTORE_NAME + os.sep, new_fs_path])
        shutil.rmtree(FILESTORE_NAME)
    else:
        logging.info(
            "The original filestore of '%s' has not been found in %s.",
            origin_db_name,
            FILESTORE_PATH,
        )
        logging.info(
            "In consequence, the filestore of the upgrade database should be restored manually."
        )


def clean_dump(dump_name):
    logging.error(
        "prevent removing dump file %s" % dump_name
    )
    # return True
    if os.path.isdir(dump_name):
        shutil.rmtree(dump_name)

    if os.path.isfile(dump_name):
        os.remove(dump_name)


def get_db_contract(dbname):
    try:
        output = subprocess.check_output(
            [
                "psql",
                dbname,
                "--no-psqlrc",
                "--tuples-only",
                "--command",
                "SELECT value FROM ir_config_parameter WHERE key = 'database.enterprise_code'",
            ]
        )
        contract = output.decode().strip()
        if contract:
            return contract
    except Exception:
        pass

    raise UpgradeError(
        "Unable to get the subscription code of your database. Your database must be registered to be "
        "eligible for an upgrade. See https://www.odoo.com/documentation/user/db_management/db_premise.html"
    )


def get_dump_basename_and_format(dump):
    """
    Return the basename and the extension of the dump.
    """
    dump_ext = next(
        (ext for ext in EXPECTED_DUMP_EXTENSIONS if dump.endswith(ext)), None
    )
    if dump_ext:
        return os.path.basename(dump)[: -len(dump_ext)], dump_ext
    elif os.path.isdir(dump):
        return get_path_basename(dump), ""

    return None, None


def is_zip_dump_valid(dump_file):
    def check_zip_integrity(f):
        try:
            if f.testzip() is not None:
                raise Exception
        except Exception:
            return False

    try:
        if zipfile.is_zipfile(dump_file):
            with zipfile.ZipFile(dump_file) as zipf:
                check_zip_integrity(zipf)

                # check that the archive contains at least the mandatory content
                if not ("dump.sql" in zipf.namelist()):
                    return False
    except Exception:
        return False
    return True


# ---------------------------------------------------------------------------------
# API management functions
# ---------------------------------------------------------------------------------


def send_json_request(request, params):
    """
    Send a JSONRPC request to the upgrade server and return its response as a dictionary
    """
    request_url = "%s/%s" % (UPGRADE_SERVER_NAME, request)

    # build the JSONRPC request
    jsonrpc_payload = {
        "jsonrpc": "2.0",
        "method": "not_used",
        "params": params,
        "id": "not_used",
    }

    request_payload = json.dumps(jsonrpc_payload).encode("utf-8")

    # build the HTTP request
    req = urlrequest.Request(
        request_url, request_payload, headers={"Content-type": "application/json"}
    )

    # send it and parse the response content
    try:
        response = urlrequest.urlopen(req, timeout=REQUEST_TIMEOUT, context=ssl_context)
        info = response.info()

        if "Content-Length" in info and int(info["Content-Length"]) > 0:
            response_data = response.read().decode("utf-8")

            # JSONRPC response
            if "application/json" in info["Content-Type"]:
                resp_payload = json.loads(response_data)

                if "result" in resp_payload:
                    if "error" in resp_payload["result"]:
                        raise UpgradeError(resp_payload["result"]["error"])
                    return resp_payload["result"]
                else:
                    error = resp_payload.get("error", {}).get("data", {}).get("message")
                    error = error or "Upgrade server bad JSONRPC response"
                    raise UpgradeError("Error: %s" % error)

            # static file response
            if "text/html" in info["Content-Type"]:
                return response_data

        # empty response
        return []

    except (urlrequest.HTTPError, urlrequest.URLError) as e:
        raise UpgradeError("Upgrade server communication error: '%s'" % e)

    except socket.timeout:
        raise UpgradeError("Upgrade server communication timeout")


def check_response_format(response, keys):
    """
    Check that a response follows the expected format (keys)
    """
    if any(k not in response for k in keys):
        raise UpgradeError(
            "The response received from the upgrade server has not the expected format (missing data: %s)"
            % ",".join([k for k in keys if k not in response])
        )


def create_upgrade_request(contract, target, aim, env_vars, ssh_key):
    """
    Create a new upgrade request using the upgrade API
    """
    logging.info("Creating new upgrade request")

    response = send_json_request(
        "upgrade/request/create",
        {
            "contract": contract,
            "target": target,
            "aim": aim,
            "actuator": "cli",
            "env_vars": env_vars,
            "ssh_key": open(ssh_key).read(),
        },
    )

    check_response_format(response, ("request_id", "token"))

    logging.info("The secret token is '%s'", response["token"])
    return response


def process_upgrade_request(token):
    """
    Start the upgrade request processing using the upgrade API
    """
    logging.info("Processing the upgrade request")
    response = send_json_request("upgrade/request/process", {"token": token})

    check_response_format(response, ("is_pg_version_compatible",))

    return response["is_pg_version_compatible"]


def start_transfer(token, ssh_key, transfer_type):
    if not os.path.isfile(ssh_key):
        raise UpgradeError("The SSH key '%s' does not exist." % ssh_key)

    response = send_json_request(
        "upgrade/request/transfer/start",
        {
            "token": token,
            "transfer_type": transfer_type,
        },
    )
    check_response_format(response, ("ssh_port",))

    if transfer_type == "download":
        check_response_format(response, ("dump_name",))

    return response


def stop_transfer(token):
    send_json_request("upgrade/request/transfer/stop", {"token": token})


def get_logs(token, from_byte=0):
    """
    Request the actual log file
    """
    request_url = "%s/%s?token=%s" % (
        UPGRADE_SERVER_NAME,
        "upgrade/request/logs",
        token,
    )
    req = urlrequest.Request(request_url, headers={"Range": "bytes=%d-" % from_byte})
    response = (
        urlrequest.urlopen(req, timeout=REQUEST_TIMEOUT, context=ssl_context)
        .read()
        .decode("utf-8")
    )
    return response


def get_request_status(token):
    """
    Request the request processing status and an optional reason
    """
    response = send_json_request("upgrade/request/status", {"token": token})
    check_response_format(response, ("status",))

    return response["status"], response.get("reason")


# ---------------------------------------------------------------------------------
# State machine handlers
# ---------------------------------------------------------------------------------


def init_handler(fsm):
    """
    Processing done in the 'init' state.
    """
    input_source, target, aim, core_count, env_vars, ssh_key = fsm.get_context_data(
        ("input_source", "target", "aim", "core_count", "env_vars", "ssh_key")
    )

    if input_source == "db":
        dbname, token_name = fsm.get_context_data(("dbname", "token_name"))
        contract = get_db_contract(dbname)
    else:
        contract, token_name = fsm.get_context_data(("contract", "token_name"))

    if ssh_key == DEFAULT_SSH_KEY_NAME:
        generate_default_ssh_keys()

    request = create_upgrade_request(
        contract, target, aim, env_vars, "%s.pub" % ssh_key
    )

    if input_source == "db":
        dump_database(dbname, get_dump_name(dbname), core_count)

    # store the token in a file to be able to resume the request in case of interruption
    save_token(token_name, target, aim, request["token"])

    fsm.update_context(request)
    return "new"


def new_handler(fsm):
    """
    Processing done in the 'new' state.
    """
    input_source, token, ssh_key = fsm.get_context_data(
        ("input_source", "token", "ssh_key")
    )
    data_server_name, data_server_user, data_server_path = fsm.get_context_data(
        ("data_server_name", "data_server_user", "data_server_path")
    )

    if input_source == "db":
        dbname = fsm.get_context_data(("dbname",))
        dump_path = get_dump_name(dbname)
        dest_dump_name = ORIGIN_DUMP_NAME
    else:
        dump_path, dump_ext = fsm.get_context_data(
            ("host_dump_upload_path", "dump_ext")
        )
        dest_dump_name = "%s%s" % (ORIGIN_DUMP_BASE_NAME, dump_ext)

    info = start_transfer(token, "%s.pub" % ssh_key, "upload")
    upload_dump(
        dump_path,
        data_server_name,
        info["ssh_port"],
        data_server_user,
        data_server_path,
        ssh_key,
        dest_dump_name,
    )
    stop_transfer(token)

    return "pending"


def pending_handler(fsm):
    """
    Processing done in the 'pending' state.
    """
    token = fsm.get_context_data(("token",))

    is_pg_version_compatible = process_upgrade_request(token)

    # if the postgres version used for the upgrade is not compatible with the client postgres
    # version used to dump the database, deactivate the upgraded database restoring.
    if not is_pg_version_compatible:
        logging.warning(
            "Your postgres version is lower than the minimal required version to restore your upgraded database. "
            "The upgraded dump will be downloaded but not restored."
        )
    fsm.update_context({"no_restore": True})

    return "progress"


def progress_handler(fsm):
    """
    Processing done in the 'progress' state.
    """
    token = fsm.get_context_data(("token",))

    status, reason = monitor_request_processing(token)

    fsm.update_context({"reason": reason})
    return status


def failed_handler(fsm):
    input_source, reason = fsm.get_context_data(("input_source", "reason"))

    if input_source == "db":
        dbname = fsm.get_context_data(("dbname",))
        clean_dump(get_dump_name(dbname))

    logging.error("The upgrade request has failed%s", ": %s" % reason if reason else "")

    return None


def cancelled_handler(fsm):
    logging.info("The upgrade request has been cancelled")
    return None


def done_handler(fsm):
    input_source, token, ssh_key, core_count, aim = fsm.get_context_data(
        ("input_source", "token", "ssh_key", "core_count", "aim")
    )
    (
        data_server_name,
        data_server_user,
        data_server_path,
        no_restore,
        dump_dest_path,
    ) = fsm.get_context_data(
        (
            "data_server_name",
            "data_server_user",
            "data_server_path",
            "no_restore",
            "host_dump_download_path",
        )
    )

    info = start_transfer(token, "%s.pub" % ssh_key, "download")
    download_dump(
        data_server_name,
        info["ssh_port"],
        data_server_user,
        data_server_path,
        info["dump_name"],
        ssh_key,
        dump_dest_path,
    )
    stop_transfer(token)

    if not no_restore:
        upgraded_db_name = fsm.get_context_data(("upgraded_db_name",))
        db_name = fsm.get_context_data(("dbname",)) if input_source == "db" else None

        restore_database(upgraded_db_name, info["dump_name"], core_count)
        restore_filestore(db_name, upgraded_db_name)
        # clean_dump(info["dump_name"])

    return None


# ---------------------------------------------------------------------------------
# Token functions (for recovering)
# ---------------------------------------------------------------------------------


def get_token_file(token_name, target, aim):
    return os.path.join(
        tempfile.gettempdir(),
        "odoo-upgrade-%s-%s-%s" % (aim, token_name, target),
    )


def save_token(token_name, target, aim, token):
    """
    Save the request token in a temporary file.
    """
    filename = get_token_file(token_name, target, aim)

    with open(filename, "w") as f:
        f.write(token)


def get_saved_token(token_name, target, aim):
    """
    Get the token of the upgrade request if it has been saved previously
    """
    filename = get_token_file(token_name, target, aim)

    try:
        with open(filename, "r") as f:
            token = f.readline()
            return token
    except Exception:
        return None


def remove_saved_token(token_name, target, aim):
    filename = get_token_file(token_name, target, aim)
    if os.path.isfile(filename):
        os.remove(filename)


# ---------------------------------------------------------------------------------
# Main functions
# ---------------------------------------------------------------------------------

fsm = StateMachine()


def monitor_request_processing(token):
    """
    Monitor the request processing status and display logs at the same time
    """
    status, reason = get_request_status(token)
    displayed_log_bytes = 0
    last_check_time = datetime.now()

    while status in ("progress", "pending"):
        # status monitoring
        if datetime.now() > last_check_time + timedelta(
            seconds=STATUS_MONITORING_PERIOD
        ):
            status, reason = get_request_status(token)
            last_check_time = datetime.now()

        # logs streaming
        if status == "progress":
            logs = get_logs(token, displayed_log_bytes)
            if logs.strip():
                logging.info(logs.strip())
                displayed_log_bytes += len(logs) - 1

        time.sleep(LOG_REFRESH_PERIOD)

    return status, reason


def parse_command_line():
    """
    Parse command-line arguments and return them
    """

    def add_upgrade_arguments(subparser):
        subparser.add_argument(
            "-d",
            "--dbname",
            help="The name of a database to dump and upgrade",
        )
        subparser.add_argument(
            "-r",
            "--restore-name",
            help="The name of database into which the upgraded dump must be restored",
        )
        subparser.add_argument(
            "-i",
            "--dump",
            help="The database dump to upgrade (.sql, .dump, .sql.gz, .zip or a psql dump directory with %s file)"
            % POSTGRES_TABLE_OF_CONTENTS,
        )
        subparser.add_argument(
            "-c",
            "--contract",
            help="The contract number associated to the database (to use with --dump only)",
        )
        subparser.add_argument(
            "-t", "--target", required=True, help="The upgraded database version"
        )
        subparser.add_argument(
            "-e",
            "--env",
            action="append",
            help="Set an environment variable, in the format VAR=VAL",
        )
        subparser.add_argument(
            "--env-file",
            type=argparse.FileType("r"),
            help="Read in a file of environment variables, one per line, in the format VAR=VAL",
        )

    def add_pg_arguments(subparser):
        subparser.add_argument(
            "-x",
            "--no-restore",
            action="store_true",
            help="Download the upgraded database dump without restoring it",
        )

    def add_common_arguments(subparser):
        subparser.add_argument(
            "-s",
            "--ssh-key",
            help="The ssh key to use for data transfer (default: %(default)s)",
            default=SSH_KEY_NAME,
        )
        subparser.add_argument(
            "-j",
            "--core-count",
            help="The number of core to use to dump/restore a database (default: %(default)s)",
            default=CORE_COUNT,
        )
        subparser.add_argument(
            "-n",
            "--data-server-name",
            help="The server name where to download/upload dumps (default: %(default)s)",
            default=DATA_SERVER_NAME,
        )
        subparser.add_argument(
            "-u",
            "--data-server-user",
            help="The server user where to download/upload dumps (default: %(default)s)",
            default=DATA_SERVER_USER,
        )
        subparser.add_argument(
            "-p",
            "--data-server-path",
            help="The path on the server where to download/upload dumps (default: %(default)s)",
            default=DATA_SERVER_PATH,
        )

    def add_token_argument(subparser):
        subparser.add_argument(
            "-t", "--token", required=True, help="The token ID of the request"
        )

    parser = argparse.ArgumentParser()

    parser.add_argument("--debug", action="store_true", help="activate debug traces")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    # sub-parser for the 'test' command
    parser_test = subparsers.add_parser(
        "test", help="upgrade a database for test purpose"
    )
    add_upgrade_arguments(parser_test)
    add_pg_arguments(parser_test)
    add_common_arguments(parser_test)

    # sub-parser for the 'production' command
    parser_prod = subparsers.add_parser(
        "production", help="upgrade a database for production purpose"
    )
    add_upgrade_arguments(parser_prod)
    add_pg_arguments(parser_prod)
    add_common_arguments(parser_prod)

    # sub-parser for the 'restore' command
    parser_restore = subparsers.add_parser(
        "restore", help="download and restore the upgraded database"
    )
    add_token_argument(parser_restore)
    parser_restore.add_argument(
        "-d",
        "--dbname",
        required=True,
        help="The local database name to retrieve the original filestore",
    )
    parser_restore.add_argument(
        "-r",
        "--restored-name",
        required=True,
        help="The database name to restore the upgraded dump",
    )
    parser_restore.add_argument(
        "--production",
        action="store_true",
        help="Indicates that it's not a test database but a production database",
    )
    add_common_arguments(parser_restore)

    # sub-parser for the 'status' command
    parser_status = subparsers.add_parser(
        "status", help="show the upgrade request status"
    )
    add_token_argument(parser_status)

    # sub-parser for the 'log' command
    parser_log = subparsers.add_parser("log", help="show the upgrade request log")
    add_token_argument(parser_log)
    parser_log.add_argument(
        "-f",
        "--from-byte",
        type=int,
        default=1,
        help="From which line start retrieving the log (1=from the beginning)",
    )

    args = parser.parse_args()

    if args.command in ("test", "production"):
        if not args.dbname and not args.dump:
            parser.error("At least a --dbname or --dump must be provided")

        if args.dump and not args.contract:
            parser.error(
                "A contract number must be provided when the --dump argument is used"
            )

    return args


def get_env_vars(env_vars, env_file):
    if env_vars is None:
        env_vars = []
    if env_file is not None:
        # Lines that start with # are treated as comments
        env_vars.extend(
            line.strip() for line in env_file if line and not line[0] == "#"
        )
    # Check that args are correctly formatted in the form VAR=VAL
    for var in env_vars:
        if not re.match(r"^\w+=\w+$", var):
            raise ValueError(
                "The following environment variable option is badly formatted: %s" % var
            )
    return env_vars


def process_upgrade_command(
    dbname, upgraded_db_name, dump, contract, target, aim, env_vars
):
    if dbname and dump:
        raise UpgradeError(
            "You cannot upgrade a database and a dump file at the same time"
        )

    start_state = "init"
    additional_context = {
        "target": target,
        "aim": aim,
        "env_vars": env_vars,
    }

    # update the context when a database is upgraded
    if dbname:
        token_name = "db_%s" % dbname
        additional_context.update(
            {
                "input_source": "db",
                "dbname": dbname,
                "upgraded_db_name": upgraded_db_name
                if upgraded_db_name
                else get_upgraded_db_name(dbname, target, aim),
                "token_name": token_name,
            }
        )

    # update the context when a dump is upgraded
    if dump:
        if not os.path.exists(dump):
            raise UpgradeError("Dump %r not found." % dump)

        dump_absolute_path = os.path.abspath(dump)
        dump_basename, dump_ext = get_dump_basename_and_format(dump)
        if dump_ext is None or (
            os.path.isdir(dump_absolute_path)
            and not os.path.isfile(
                os.path.join(dump_absolute_path, POSTGRES_TABLE_OF_CONTENTS)
            )
        ):
            raise UpgradeError(
                "The database dump must be in one of the following formats: %s. "
                "It can also be a directory dump (containing the file %s)."
                % (", ".join(EXPECTED_DUMP_EXTENSIONS), POSTGRES_TABLE_OF_CONTENTS)
            )

        if dump_ext == ".zip" and not is_zip_dump_valid(dump):
            raise UpgradeError(
                "The zip dump archive is not valid (either corrupted or does not contain, at least, a dump.sql file)"
            )

        token_name = get_token_name(dump_absolute_path)
        additional_context.update(
            {
                "input_source": "dump",
                "token_name": token_name,
                "dump_basename": dump_basename,
                "dump_ext": dump_ext,
                "contract": contract,
                "no_restore": True,
            }
        )

    # if this upgrade request has been interrupted, try to resume it
    saved_token = get_saved_token(token_name, target, aim)

    if saved_token is not None:
        logging.info(
            "This upgrade request seems to have been interrupted. Do you want to resume it ? [Y/n]"
        )
        if user_confirm():
            logging.info("Resuming the upgrade request")

            start_state, reason = get_request_status(saved_token)
            additional_context.update({"token": saved_token, "reason": reason})
        else:
            logging.info("Restarting the upgrade request from the beginning")

    # run the upgrade
    fsm.run(start_state, additional_context)

    # cleaning
    if dbname:
        clean_dump(get_dump_name(dbname))
    remove_saved_token(token_name, target, aim)


def get_token_name(dump_absolute_path):
    input_file = (
        os.path.join(dump_absolute_path, "toc.dat")
        if os.path.isdir(dump_absolute_path)
        else dump_absolute_path
    )

    heuristics = (
        input_file,
        os.path.getsize(input_file),
        os.path.getctime(input_file),
        os.getuid(),
    )
    sha = hashlib.sha256()
    for heuristic in heuristics:
        sha.update(str(heuristic).encode() + b"\x1e")
    return "dump_%s" % sha.hexdigest()


def process_restore_command(token, dbname, aim, restored_name):
    status, _ = get_request_status(token)
    if status == "done":
        fsm.run(
            "done",
            {
                "token": token,
                "aim": aim,
                "dbname": dbname,
                "upgraded_db_name": restored_name,
                "no_restore": False,
            },
        )


def process_status_command(token):
    status, reason = get_request_status(token)
    logging.info(
        "Request status: %s%s", status.upper(), " (%s)" % reason if reason else ""
    )


def process_log_command(token, from_byte):
    logs = get_logs(token, from_byte)
    for log in logs.split("\n")[:-1]:
        logging.info(log)


def main():
    args = parse_command_line()

    if args.dump:
        dump_absolute_path = os.path.abspath(args.dump)

        """
        If the table of contents path is passed, change the directory and path to the parent of the table of
        contents so that rsync can send the whole directory without any issues
        """
        if get_path_basename(dump_absolute_path) == POSTGRES_TABLE_OF_CONTENTS:
            host_dump_upload_path = get_path_nth_parent(dump_absolute_path, 1)
            host_dump_download_path = get_path_nth_parent(dump_absolute_path, 2)
            args.dump = host_dump_upload_path
        else:
            host_dump_upload_path = dump_absolute_path
            host_dump_download_path = get_path_nth_parent(dump_absolute_path, 1)
    else:
        host_dump_upload_path = "."
        host_dump_download_path = "."

    # configure loggers
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %I:%M:%S",
        level=log_level,
    )

    # define state machine and internal context
    fsm.set_states(
        {
            "init": init_handler,
            "new": new_handler,
            "pending": pending_handler,
            "progress": progress_handler,
            "done": done_handler,
            "failed": failed_handler,
            "cancelled": cancelled_handler,
        }
    )

    try:
        # handle parameters specific to some commands
        if args.command in ("test", "production", "restore"):
            fsm.update_context(
                {
                    "ssh_key": args.ssh_key,
                    "core_count": args.core_count,
                    "data_server_name": args.data_server_name,
                    "data_server_user": args.data_server_user,
                    "data_server_path": args.data_server_path,
                    "host_dump_upload_path": host_dump_upload_path,
                    "host_dump_download_path": host_dump_download_path,
                }
            )

        if args.command in ("test", "production"):
            fsm.update_context(
                {
                    "no_restore": args.no_restore,
                }
            )

        if args.command in ("test", "production"):
            env_vars = get_env_vars(args.env, args.env_file)
            process_upgrade_command(
                args.dbname,
                args.restore_name,
                args.dump,
                args.contract,
                args.target,
                args.command,
                env_vars,
            )

        elif args.command == "restore":
            aim = "production" if args.production else "test"
            process_restore_command(args.token, args.dbname, aim, args.restored_name)

        elif args.command == "status":
            process_status_command(args.token)

        elif args.command == "log":
            process_log_command(args.token, args.from_byte)

    except (UpgradeError, StateMachine.Error) as e:
        input(e)
        logging.error("Error: %s", e)

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
