# Send Kiron's evaluation PDF and targeted CV PDF by Gmail SMTP.

from __future__ import annotations

import argparse
from email.message import EmailMessage
import mimetypes
import os
from pathlib import Path
import smtplib
import sys

from dotenv import load_dotenv


def _require_file(path: Path, label: str) -> Path:
    """Validate one required attachment file."""
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")
    return resolved


def _attach_file(message: EmailMessage, path: Path, filename: str) -> None:
    """Attach one file using a guessed MIME type."""
    mime_type, _ = mimetypes.guess_type(path.name)

    if mime_type:
        maintype, subtype = mime_type.split("/", 1)
    else:
        maintype, subtype = "application", "octet-stream"

    message.add_attachment(
        path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        filename=filename,
    )


def send_result_email(
    recipient_email: str,
    evaluation_pdf_path: str,
    cv_pdf_path: str,
) -> None:
    """Send Kiron's two final PDFs to one recipient."""
    load_dotenv()

    sender = os.environ.get("GMAIL_SENDER_EMAIL")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender:
        raise RuntimeError("Missing GMAIL_SENDER_EMAIL in environment.")

    if not app_password:
        raise RuntimeError("Missing GMAIL_APP_PASSWORD in environment.")

    recipient = recipient_email.strip()

    if not recipient or "@" not in recipient:
        raise ValueError("Recipient email address is missing or invalid.")

    evaluation_pdf = _require_file(
        Path(evaluation_pdf_path),
        "Evaluation PDF",
    )
    cv_pdf = _require_file(
        Path(cv_pdf_path),
        "CV PDF",
    )

    message = EmailMessage()
    message["From"] = f"Kiron CV Assistant <{sender}>"
    message["To"] = recipient
    message["Subject"] = "Your Kiron job application results 🦕"

    message.set_content(
        """Hi dear job seeker,

Kiron has finished reviewing your job application materials.

Attached you will find:

- your job-match evaluation
- your targeted CV
If you'd like to use your own AI model or API for stronger reasoning and greater privacy, add an editing and review layer before finalizing your documents, create your own CV layout, or build a local intelligence system to manage your CV materials, feel free to reply to this email to reach the developer.

Thank you for trying Kiron.

— Kiron 🦕
"""
    )

    _attach_file(
        message,
        evaluation_pdf,
        "kiron_evaluation.pdf",
    )
    _attach_file(
        message,
        cv_pdf,
        "kiron_targeted_cv.pdf",
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(message)

    print(f"✓ Kiron results sent to {recipient}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Send Kiron's evaluation PDF and targeted CV PDF "
            "through the configured Gmail account."
        )
    )
    parser.add_argument("recipient_email", help="Destination email address")
    parser.add_argument("evaluation_pdf_path", help="Path to evaluation.pdf")
    parser.add_argument("cv_pdf_path", help="Path to cv.pdf")

    args = parser.parse_args()

    send_result_email(
        recipient_email=args.recipient_email,
        evaluation_pdf_path=args.evaluation_pdf_path,
        cv_pdf_path=args.cv_pdf_path,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
