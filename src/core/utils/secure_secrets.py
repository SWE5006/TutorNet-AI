import os, boto3

# Load from SSM
def load_secret_into_env(force: bool = False) -> str:

    existing = os.getenv("OPENAI_API_KEY")
    if existing and not force:
        return existing

    print("[secure_secrets] load_secret_into_env called")
    region = os.getenv("AWS_REGION")
    if not region:
        raise RuntimeError("AWS_REGION is missing and boto3 cannot initialize")
    ssm = boto3.client("ssm", region)
    resp = ssm.get_parameter(
        Name=os.getenv("AWS_PARAM_NAME"),
        WithDecryption=True
    )
    value = resp["Parameter"]["Value"]
    os.environ["OPENAI_API_KEY"] = value
    return value
