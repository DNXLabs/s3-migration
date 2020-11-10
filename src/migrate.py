import os
import time
import json
import subprocess
from datetime import datetime
from termcolor import colored


def read_config(mapping_file):

    data = {}

    try:
        with open(mapping_file, 'r') as file:
            data = json.load(file)

    except Exception as error:
        print(
            "An exception occurred while loading the mapping:\n{}"
            .format(error)
        )

    finally:
        file.close()

    return data


def prepare_log_folder(start_date, sync_id):

    folder1 = start_date.strftime("%Y-%m-%d_%H:%M:%S")
    folder2 = sync_id

    path = "./logs/{}/{}/".format(folder1, folder2)
    os.makedirs(path, exist_ok=True)

    return path


def copy_to_s3(log_path, mapping, test_mode):

    additional_commands = []
    s3sync = "aws s3 sync %s %s %s >> %s"

    if test_mode:
        additional_commands.append("--dryrun")

    if mapping["exclude"]:
        for exclude in mapping["exclude"]:
            additional_commands.append("--exclude=\"{}\"".format(exclude))

    if mapping["include"]:
        for exclude in mapping["include"]:
            additional_commands.append("--include=\"{}\"".format(exclude))

    extra_commands = " ".join(additional_commands)
    log_output = log_path + "files_finished.txt"

    command = s3sync \
        % (mapping["source"],
           mapping["target"],
           extra_commands,
           log_output)

    print(
        colored("Mapping ID: ", "yellow") + mapping["id"] + " / " +
        colored("s3sync command: ", "yellow") + command
    )

    try:
        # Executes command and returns stdout and stderr while running...
        for log in execute_command(command):
            print(log, end="")
            send_log(log_path, log)

    except Exception as error:
        print(colored(error, "red"))
        send_log(log_path, error)
        exit(1)


def execute_command(command):

    popen = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True)

    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()

    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def send_log(log_path, log):

    with open(log_path + '/header.txt', 'w') as f:
        print(log, file=f)  # Python 3.x


def main():
    start_time = time.time()
    start_date = datetime.now()

    print(
        colored('Sync started at {}'.format(start_date), "green")
    )

    # Read the mapping configuration from CSV file
    config = read_config('./mapping.json')
    test_mode = config["test"]

    for mapping in config["mapping"]:
        # Prepare folder with relevant logs
        log_path = prepare_log_folder(start_date, mapping["id"])

        # Copy to S3 bucket via AWS CLI s3 sync command
        copy_to_s3(log_path, mapping, test_mode)

    end_date = datetime.now()
    print(
        colored('Sync finished at {}'.format(end_date), "green")
    )
    print(
        colored('Sync concluded in {} seconds'.format(
            time.time() - start_time
        ), "green")
    )


if __name__ == '__main__':
    main()
