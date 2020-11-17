import json
import csv
import logging
from template import MAPPING_TEMPLATE


def read_csv(file_name, logger):

    data = {}

    try:
        with open(file_name, newline='') as file:
            reader = csv.reader(file)
            data = list(reader)
            file.close()

    except FileNotFoundError:
        logger.error("File {} not found".format(file_name))
        exit(1)

    except Exception as error:
        logger.error(
            "An exception occurred while loading job_ids list:\n{}"
            .format(error)
        )
        exit(1)

    return data


def save_json(content, file_name, logger):

    try:
        with open(file_name, 'w') as file:
            json.dump(content, file, indent=4)
            file.close()

            logger.info(
                "File {} created with success"
                .format(file_name)
            )

    except Exception as error:
        logger.error(
            "An exception occurred while saving {}:\n{}"
            .format(file_name, error)
        )
        exit(1)


def setup_logger(name, level=logging.INFO):

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)8s %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)

    logger.setLevel(level)
    logger.addHandler(console_handler)

    return logger


def main(csv_file='./mapping/job_ids.csv', json_file='./mapping/mapping.json'):

    output = {
        "test": "true",
        "mapping": []
    }

    logger = setup_logger("main")

    # Read the mapping configuration from CSV file
    job_ids = read_csv(csv_file, logger)

    # Prepare output for all the job ids configured
    for job_id in job_ids:
        mapping = MAPPING_TEMPLATE
        mapping = mapping.replace("{{job_id}}", job_id[0])
        mapping = json.loads(mapping)

        # Print the mapping while in debug mode
        logger.debug(mapping)

        # Add the mapping to the file output
        output["mapping"].append(mapping)

    # Save mapping.json file
    save_json(output, json_file, logger)


if __name__ == '__main__':
    main()
