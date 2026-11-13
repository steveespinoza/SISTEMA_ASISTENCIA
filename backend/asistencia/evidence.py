import hashlib
from io import BytesIO
from uuid import UUID

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

MAX_PHOTO_BYTES = 12 * 1024 * 1024
MAX_PHOTO_PIXELS = 50_000_000


class InvalidPhoto(ValueError):
    pass


class PhotoStorageUnavailable(Exception):
    pass


def prepare_photo(upload: FileStorage) -> bytes:
    data = upload.stream.read(MAX_PHOTO_BYTES + 1)
    if len(data) > MAX_PHOTO_BYTES:
        raise InvalidPhoto("La foto supera el límite de 12 MB.")
    try:
        with Image.open(BytesIO(data), formats=["JPEG", "PNG", "WEBP"]) as source:
            if source.width * source.height > MAX_PHOTO_PIXELS:
                raise InvalidPhoto("La resolución de la foto es demasiado grande.")
            if getattr(source, "is_animated", False):
                raise InvalidPhoto("Selecciona una foto sin animación.")
            photo = ImageOps.exif_transpose(source)
            photo.thumbnail((1600, 1600))
            photo = photo.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise InvalidPhoto("Selecciona una foto válida en JPG, PNG o WebP.") from error

    photo.info.clear()
    output = BytesIO()
    photo.save(output, format="WEBP", quality=82)
    return output.getvalue()


class PhotoStorage:
    def __init__(self, bucket: str, region: str | None) -> None:
        self.bucket = bucket
        self.region = region
        self._client = None

    def client(self):
        if self._client is None:
            self._client = boto3.session.Session().client(
                "s3",
                region_name=self.region,
                config=Config(
                    signature_version="s3v4",
                    connect_timeout=3,
                    read_timeout=8,
                    retries={"mode": "standard", "total_max_attempts": 2},
                ),
            )
        return self._client

    def save(self, account_id: UUID, request_key: UUID, upload: FileStorage) -> str:
        photo = prepare_photo(upload)
        digest = hashlib.sha256(photo).hexdigest()
        key = f"asistencia/evidencias/{account_id}/{request_key}/{digest}.webp"
        try:
            self.client().put_object(
                Bucket=self.bucket,
                Key=key,
                Body=photo,
                ContentType="image/webp",
                CacheControl="private, no-store",
                ServerSideEncryption="AES256",
                IfNoneMatch="*",
            )
        except ClientError as error:
            if error.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 412:
                raise PhotoStorageUnavailable from error
            # Un intento anterior ya guardó exactamente el mismo contenido.
        except BotoCoreError as error:
            raise PhotoStorageUnavailable from error
        return key

    def access_url(self, key: str) -> str:
        try:
            return self.client().generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=60,
            )
        except (BotoCoreError, ClientError) as error:
            raise PhotoStorageUnavailable from error
