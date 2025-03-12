from infisical_sdk import InfisicalSDKClient
from dotenv import load_dotenv
import os

load_dotenv()

INFISICAL_ID = os.getenv('INFISICAL_ID')
INFISICAL_SECRET = os.getenv('INFISICAL_SECRET')
INFISICAL_HOST = os.getenv('INFISICAL_HOST')
INFISICAL_PROJECT_ID = os.getenv('INFISICAL_PROJECT_ID')

client = InfisicalSDKClient(host=INFISICAL_HOST)
client.auth.universal_auth.login(
    client_id=INFISICAL_ID,
    client_secret=INFISICAL_SECRET
)


def infisical_get_secret(secret_name: str, mode: str = 'prod') -> str:
    """Получение секрета из учетной записи Infisical
    :param secret_name: название секрета
    :param mode: режим работы (dev, prod)
    :return: значение секрета"""
    return client.secrets.get_secret_by_name(
        secret_name=secret_name,
        project_id=INFISICAL_PROJECT_ID,
        environment_slug=mode,
        secret_path="/"
    ).secretValue


if __name__ == '__main__':
    print(infisical_get_secret(secret_name="WEBHOOK"))
