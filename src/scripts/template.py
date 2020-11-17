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
