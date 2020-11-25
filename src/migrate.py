import os
import time
import json
import csv
import subprocess
import logging
import collections
import functools
import operator
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


def check_invalid_mapping(config, logger):

    invalid = False

    if "test" not in config:
        logger.error("Mandatory attribute \"test\" is missing")
        invalid = True

    if "mapping" not in config:
        logger.error("Mandatory attribute \"mapping\" is missing")
        invalid = True
    else:
        for idx, mapping in enumerate(config["mapping"]):
            if "id" not in mapping:
                logger.error(
                    "Mandatory attribute \"id\"" +
                    " missing for item {}".format(idx))
                invalid = True

            if "source" not in mapping:
                logger.error(
                    "Mandatory attribute \"source\"" +
                    " missing for item {}".format(idx))
                invalid = True

            if "target" not in mapping:
                logger.error(
                    "Mandatory attribute \"target\"" +
                    " missing for item {}".format(idx))
                invalid = True

    return invalid


def prepare_log_folder(start_date, subprocess_id=""):

    folder_date = start_date.strftime("%Y-%m-%d_%H-%M-%S")

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
        '%(name)-20s: %(levelname)8s %(message)s')

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

    if mapping["test_mode"] is True:
        additional_commands.append("--dryrun")

    if "exclude" in mapping:
        for exclude in mapping["exclude"]:
            additional_commands.append("--exclude=\"{}\"".format(exclude))

    if "include" in mapping:
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
            logger.info(log.strip())

    except Exception as error:
        logger.error(error)

    finally:
        logger.info('Migration concluded')
        logger.info('Parsing log files...')

        counter = parse_file_processed(log_output, logger)

        logger.info('Subprocess concluded in {} seconds'.format(
            time.time() - start_time))

        logger.info('Subprocess finished')

        return counter


def parse_file_processed(log_file, logger):

    counter = {}

    try:
        csv_file_name = log_file.replace(".txt", ".csv")

        # Create .csv file with conversion
        csv_file = open(csv_file_name, 'w', newline='')
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow(["Action", "Source", "Target"])

        # Open .txt file with list of files processed
        txt_file = open(log_file, 'r')
        lines = txt_file.readlines()

        for line in lines:
            # Ignore empty lines
            if not line:
                continue

            # Strips the newline character
            original = line.strip()

            # Remove dryrun message (only for tests)
            formatted = original.replace("(dryrun) ", "")

            # Separate the action from the rest of the log
            action, formatted = formatted.split(": ", 1)

            # Split source and target
            results = formatted.split(" to ")

            # Exception scenario where " to " is also part of the filename
            if len(results) > 2:
                length = len(results)
                mean = int(length / 2)

                source = " to ".join(results[0:mean])
                target = " to ".join(results[mean:length])
            else:
                source = results[0]
                target = results[1]

            logger.debug(
                "Action: " + action + "\n" +
                "Source: " + source + "\n" +
                "Target: " + target)

            # Count the total of files based on action
            if action in counter:
                counter[action] += 1
            else:
                counter[action] = 1

            # Write content to .csv file
            writer.writerow([action, source, target])

        # Output total of files processed
        if counter:
            logger.info("Total files processed:")
            for key, value in counter.items():
                logger.info("\t{} = {}".format(key, value))
        else:
            logger.info("No files pending for processing")

    except FileNotFoundError:
        logger.error("File {} not found".format(log_file))

    except Exception as error:
        logger.error(
            "An exception occurred while loading the processed files:\n{}"
            .format(error)
        )

    finally:
        txt_file.close()
        csv_file.close()

    return counter


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

    # Read the mapping configuration from json file
    config = read_config(mapping_file, logger)

    logger.info('Validate mapping configuration...')

    # Check if mandatory attributes are available
    if check_invalid_mapping(config, logger):
        logger.info('Sync finished due to missing attributes')
        exit(1)

    # Adjust mapping for individual processing and create log folders
    for mapping in config["mapping"]:
        # Add variable for test mode
        mapping["test_mode"] = config["test"]
        # Prepare log folder for individual subprocess
        mapping["log_folder"] = prepare_log_folder(start_date, mapping["id"])

    pool = Pool(10)
    results = pool.map(copy_to_s3, config["mapping"])

    # Calculate total count by aggregating all of the results
    total_count = dict(
        functools.reduce(
            operator.add,
            map(
                collections.Counter,
                results
            )
        )
    )

    # Output total of files processed
    if total_count:
        logger.info("Grand total of files processed:")
        for key, value in total_count.items():
            logger.info("\t{} = {}".format(key, value))
    else:
        logger.info("No files pending for processing")

    # Close the multiprocessing pool
    pool.close()

    logger.info(
        'Sync concluded in {} seconds'.format(time.time() - start_time))

    logger.info('Sync finished')


if __name__ == '__main__':
    main()
