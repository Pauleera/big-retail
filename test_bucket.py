import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def test_aws_credentials():
    try:
        s3 = boto3.client("s3")
        response = s3.list_buckets()
        print("✅ ¡Conexión exitosa a AWS!")
        print("Tus buckets de S3:")
        for bucket in response["Buckets"]:
            print(" -", bucket["Name"])
    except NoCredentialsError:
        print("❌ No se encontraron credenciales de AWS.")
    except PartialCredentialsError:
        print("❌ Credenciales incompletas de AWS.")
    except Exception as e:
        print("❌ Otro error ocurrió:", str(e))

# Ejecutar prueba
test_aws_credentials()
