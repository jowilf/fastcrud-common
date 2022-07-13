import re


def slugify_class_name(name: str) -> str:
    return "_".join(
        re.sub(
            "([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1", name.replace("-", " "))
        ).split()
    ).lower()


def get_file_icon(mime_type):
    mapping = {
        "image": "fa-file-image",
        "audio": "fa-file-audio",
        "video": "fa-file-video",
        "application/pdf": "fa-file-pdf",
        "application/msword": "fa-file-word",
        "application/vnd.ms-word": "fa-file-word",
        "application/vnd.oasis.opendocument.text": "fa-file-word",
        "application/vnd.openxmlformatsfficedocument.wordprocessingml": "fa-file-word",
        "application/vnd.ms-excel": "fa-file-excel",
        "application/vnd.openxmlformatsfficedocument.spreadsheetml": "fa-file-excel",
        "application/vnd.oasis.opendocument.spreadsheet": "fa-file-excel",
        "application/vnd.ms-powerpoint": "fa-file-powerpoint",
        "application/vnd.openxmlformatsfficedocument.presentationml": "fa-file-powerpoint",
        "application/vnd.oasis.opendocument.presentation": "fa-file-powerpoint",
        "text/plain": "fa-file-text",
        "text/html": "fa-file-code",
        "text/csv": "fa-file-csv",
        "application/json": "fa-file-code",
        "application/gzip": "fa-file-archive",
        "application/zip": "fa-file-archive",
    }
    for key in mapping:
        if key in mime_type:
            return mapping[key]
    return "fa-file"
