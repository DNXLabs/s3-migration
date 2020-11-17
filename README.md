# S3 File Migration

Python script for file migration between EC2 and S3.

## How to trigger a new migration

There are 2 main steps required to perform a file migration:

1. Configure the `mapping.json` file with your sources and targets.
2. Run the command:

```
make migrate
```

## Configuration of file mapping

In the root folder there is a file `mapping.json` which holds the mapping between the EC2 file systems (source) and the S3 bucket(s) (target).

The file has 2 main global attributes:

- **test** (`mandatory`): Identifies if the script runs the sync in test mode or if proceeds with the real transfer.
- **mapping** (`mandatory`): List of items with the mappings for S3 sync command.

Each item from **mapping** attribute contains:

- **source** (`mandatory`): name of the folder to be migrated, the script will list all the files inside of this folder including all subfolders (recursive search).
- **include** (`optional`): a list of strings which define files to be included (multiple items allowed).
- **exclude** (`optional`): a list of strings which define files to be excluded (multiple items allowed).
- **target** (`mandatory`): name of the S3 bucket which will receive the files, it can include sub-folders in the name.

Example:

```
{
    "test": true,
    "mapping": [
        {
            "id": "global",
            "source": "./files",
            "include": [],
            "exclude": [
                "*folder1/*",
                "*folder3/*"
            ],
            "target": "s3://my_bucket/"
        },
        {
            "id": "folder1",
            "source": "./files/folder1",
            "include": [],
            "exclude": [],
            "target": "s3://my_bucket/new_folder_1"
        }
    ]
}
```

## Generate your mapping file dynamically

1. Create a file in `./mapping/job_ids.csv` with a single column where each line represents an identifier for each job.

E.g.
```
job_1
job_2
job_n
```

2. Adjust the constant MAPPING_TEMPLATE in the file `./src/mapping/template.py` and use the attribute `{{job_id}}` as a tag for automatic replacement. Each line in your .csv file is going to generate a new item in the mapping section of the `mapping.json` file. For example:

The following config...

```
MAPPING_TEMPLATE = """
{
    "id": "{{job_id}}",
    "source": "/{{job_id}}/uploads/images",
    "include": [],
    "exclude": [
        "*folder1/*",
        "*folder3/*"
    ],
    "target": "s3://my_bucket/{{job_id}}/images"
}
"""
```

... plus the `job_ids.csv` file from above would result in the following `mapping.json` configuration:

```
{
    "test": "true",
    "mapping": [
        {
            "id": "job_1",
            "source": "/job_1/uploads/images",
            "include": [],
            "exclude": [
                "*folder1/*",
                "*folder3/*"
            ],
            "target": "s3://my_bucket/job_1/images"
        },
        {
            "id": "job_2",
            "source": "/job_2/uploads/images",
            "include": [],
            "exclude": [
                "*folder1/*",
                "*folder3/*"
            ],
            "target": "s3://my_bucket/job_2/images"
        },
        {
            "id": "job_n",
            "source": "/job_n/uploads/images",
            "include": [],
            "exclude": [
                "*folder1/*",
                "*folder3/*"
            ],
            "target": "s3://my_bucket/job_n/images"
        }
    ]
}
```

3. After your configuration is concluded just type the command below to generate the `mapping.json` file:

```
make mapping
```

## Dependencies

- Python 3
    - pip
    - venv
- AWS CLI