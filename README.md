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

## Dependencies

- Python 3
    - pip
    - venv
- AWS CLI