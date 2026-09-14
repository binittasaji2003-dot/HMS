"""Security and validation utilities for Candidate documents and file uploads."""
import os
from django.core.exceptions import ValidationError

# Configuration constants
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/pjpeg",
    "image/png",
    "image/x-png",
}
FORBIDDEN_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".bash", ".zsh", ".bin",
    ".msi", ".dll", ".so", ".dylib", ".com", ".scr", ".pif",
    ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".ps1",
    ".py", ".pyc", ".pyw", ".php", ".phtml", ".php3", ".php4",
    ".php5", ".asp", ".aspx", ".cgi", ".pl", ".jar", ".war",
}


def validate_document_file(file_obj):
    """
    Validates uploaded candidate documents:
    1. Rejects null/empty files.
    2. Validates maximum file size (10 MB).
    3. Validates file extension (PDF, JPG, JPEG, PNG only).
    4. Explicitly blocks executable and script extensions.
    5. Validates Content-Type header if present.
    6. Inspects magic bytes/file header to block disguised executables (PE, ELF, scripts).
    """
    if not file_obj:
        raise ValidationError("No file was uploaded.")

    # 1. Size check
    if file_obj.size > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise ValidationError(f"File size exceeds the maximum allowed limit of {max_mb}MB.")

    if file_obj.size == 0:
        raise ValidationError("Uploaded file is empty (0 bytes).")

    # 2. Extension check
    filename = getattr(file_obj, "name", "")
    _, ext = os.path.splitext(filename.lower())

    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File format '{ext}' is not permitted. Only PDF, JPG, JPEG, and PNG files are allowed."
        )

    if ext in FORBIDDEN_EXTENSIONS:
        raise ValidationError("Executable or executable script files are strictly prohibited.")

    # 3. Content-Type check (if provided by client/browser)
    content_type = getattr(file_obj, "content_type", "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES and content_type != "application/octet-stream":
        raise ValidationError(
            f"Invalid file content type '{content_type}'. Allowed types are PDF, JPG, JPEG, and PNG."
        )

    # 4. Binary signature / Magic Byte check
    try:
        current_pos = file_obj.tell() if hasattr(file_obj, "tell") else 0
        file_obj.seek(0)
        header = file_obj.read(16)
        file_obj.seek(current_pos)
    except Exception:
        header = b""

    # Detect dangerous executable signatures
    if header.startswith(b"MZ"):
        raise ValidationError("Executable files (DOS/Windows PE) are strictly prohibited.")
    if header.startswith(b"\x7fELF"):
        raise ValidationError("Executable files (Linux ELF) are strictly prohibited.")
    if header.startswith(b"#!"):
        raise ValidationError("Shell script files are strictly prohibited.")

    # Verify matching header for expected file type
    if ext == ".pdf":
        if not header.startswith(b"%PDF"):
            raise ValidationError("File content is not a valid PDF document.")
    elif ext in {".jpg", ".jpeg"}:
        if not header.startswith(b"\xff\xd8"):
            raise ValidationError("File content is not a valid JPEG/JPG image.")
    elif ext == ".png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValidationError("File content is not a valid PNG image.")

    return file_obj
