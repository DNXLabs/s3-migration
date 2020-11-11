import os
import time
import json
import subprocess
import logging
from datetime import datetime
from multiprocessing import Pool


def read_config(mapping_file, logger):

    data = {}

    try:
        with open(mapping_file, 'r') as file:
            data = json.load(file)

    except FileNotFoundError:
        logger.error("File {} not found".format(mapping_file))
        exit(1)

    except Exception as error:
        logger.error(
            "An exception occurred while loading the mapping:\n{}"
            .format(error)
        )
        exit(1)

    finally:
        file.close()

    return data


def prepare_log_folder(start_date, subprocess_id=""):

    folder_date = start_date.strftime("%Y-%m-%d_%H:%M:%S")

    if subprocess_id:
        path = "./logs/{}/{}/".format(folder_date, subprocess_id)
    else:
        path = "./logs/{}/".format(folder_date)

    os.makedirs(path, exist_ok=True)

    return path


def setup_logger(name, log_file, level=logging.INFO):

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)8s %(message)s')

    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    formatter = logging.Formatter(
        '%(name)-12s: %(levelname)8s %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)

    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def copy_to_s3(mapping):

    start_time = time.time()

    logger = setup_logger(
        mapping["id"], mapping["log_folder"] + "/logfile.log")

    logger.info('Subprocess started')

    additional_commands = []
    s3sync = "aws s3 sync %s %s %s --no-progress >> %s"

    if mapping["test_mode"]:
        additional_commands.append("--dryrun")

    if mapping["exclude"]:
        for exclude in mapping["exclude"]:
            additional_commands.append("--exclude=\"{}\"".format(exclude))

    if mapping["include"]:
        for exclude in mapping["include"]:
            additional_commands.append("--include=\"{}\"".format(exclude))

    extra_commands = " ".join(additional_commands)
    log_output = mapping["log_folder"] + "files_processed.txt"

    command = s3sync \
        % (mapping["source"],
           mapping["target"],
           extra_commands,
           log_output)

    logger.info('Subprocess command {}'.format(command))

    try:
        # Executes command and returns stdout and stderr while running...
        for log in execute_command(command):
            logger.info(log)

    except Exception as error:
        logger.error(error)

    finally:
        logger.info('Subprocess concluded in {} seconds'.format(
            time.time() - start_time))

        logger.info('Subprocess finished')


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


def execute_command_in_background(command):

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True
    )

    return result


def main(mapping_file='./mapping.json'):
    start_time = time.time()
    start_date = datetime.now()

    # Prepare log folder for main program
    log_folder = prepare_log_folder(start_date)

    logger = setup_logger(
        "main", log_folder + "/logfile.log")

    logger.info('Sync started')

    # Read the mapping configuration from CSV file
    config = read_config(mapping_file, logger)

    # Adjust mapping for individual processing and create log folders
    for mapping in config["mapping"]:
        # Add variable for test mode
        mapping["test_mode"] = config["test"]
        # Prepare log folder for individual subprocess
        mapping["log_folder"] = prepare_log_folder(start_date, mapping["id"])

    pool = Pool(10)
    pool.map(copy_to_s3, config["mapping"])

    logger.info(
        'Sync concluded in {} seconds'.format(time.time() - start_time))

    logger.info('Sync finished')


if __name__ == '__main__':
    main()
