# Internship Certificate Generator

A Streamlit application that creates personalized internship certificates from
an Excel roster, emails selected certificates, and records the result of each
attempt.

## Project layout

```text
certificate_generator/
  certificates.py       Certificate image generation
  emailing.py           Gmail SMTP connection and email composition
  processing.py         Batch previews, UIDs, expiry, and delivery report
  personalize_template.py Pillow certificate renderer and single-certificate CLI
  create_sample_excel.py
inputs/
  template.png          Default certificate artwork
  signature.png         Source signature artwork
outputs/                One folder per processing run
tests/
main.py                 Streamlit entry point
generate_certificate.py Standalone single-certificate command
pyproject.toml
requirements.txt
```

## Setup and run

Use Python 3.10 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run main.py
```

Upload an `.xlsx` workbook with `Name`, `Email`, `Send`, and `Duration`
columns. Each row's `Duration` is printed on that student's certificate.
Column names are case-insensitive; `student_name`, `student_email`,
`send_email`, and `workshop_duration` are also accepted. Use `yes` in `Send`
for recipients who should receive an email; other values are skipped.

The standalone certificate script uses `inputs/template.png`. The Streamlit app
can also use a template image uploaded in the UI. The sender address is
configured in the application; the app password is read from the project-root
`.env` file.
Add this entry to `.env` without quotes:

```text
APP_PASSWORD=your_gmail_app_password
```

For a starting template, copy `.env.sample` to `.env` and set values locally.
Never commit `.env`; enter production values in the hosting provider's secret
settings instead.

The `.env` file is ignored by Git. The app password is not displayed in the GUI
or included in run reports. Restart the Streamlit app after changing `.env`.
If no student row is marked `yes`, the app does not require the password.
The provided student workbook is excluded from Git because it contains
recipient information. Upload your workbook in the app; the sample workbook can
be recreated locally with `python -m certificate_generator.create_sample_excel`.

## Unique IDs, previews, and certificate links

The app generates a globally unique UID for each certificate. It first creates
the certificates and displays every preview. Email is only sent after you
approve each selected recipient's preview and click the explicit send button.
The UID, row-specific duration, verification URL, and six-month expiry are in
the run's recipient report.

When deployed, a verification link points back to this app with the certificate
UID. The app serves the certificate only while its six-month registry record
has not expired. Anyone who obtains a link can view that certificate; it is a
bearer link, not access restricted to the recipient's email account.

Set `APP_PUBLIC_URL` to the deployed HTTPS base URL in the hosting provider's
secret/environment settings (or `.env` for local testing). On Render, the app
can also use the platform-provided `RENDER_EXTERNAL_URL`. Generate a new batch
after deployment so certificates and email messages contain the hosted URL.
Certificates created earlier with localhost URLs must be regenerated.

The public management UI requires `APP_ADMIN_PASSWORD` in the host's secret
settings. Certificate links remain accessible without that admin password.
Never commit `.env` or paste secrets into chat. Configure `APP_PASSWORD` in the
host's secret settings for Gmail SMTP; hosting providers may restrict SMTP.

This app stores certificates and their expiry registry in `outputs/`. A
deployment must mount durable persistent storage there or the public links will
break after restarts/redeploys. It must also permit outbound SMTP on port 587.
For example, Render documents that its free web services lose local files when
they restart or spin down, and block outbound SMTP on port 587; therefore that
free plan is not suitable for this workflow. See [Render's free-instance
limitations](https://render.com/docs/free). A paid service with a persistent
disk may be required. Do not expose the management UI without configuring
`APP_ADMIN_PASSWORD`; use a host that supports private source repositories and
configure the admin password and SMTP secret before enabling sending.

## Run output

Each processing run creates a uniquely named folder in `outputs/` containing:

```text
<run-id>/
  certificates/          Individual generated certificates
  certificates.zip       Downloadable archive
  delivery_report.csv    One row per student and email outcome
```

The report records whether a certificate was generated, whether an email was
sent, skipped, or failed, and any associated error. A `sent` result means the
SMTP server accepted the message; it cannot confirm delivery to the recipient's
inbox.

To recreate the example workbook:

```powershell
python -m certificate_generator.create_sample_excel
```

## Generate a single personalized certificate

Run the standalone Pillow script to fill the supplied template's certificate
number, student name, duration, and verification URL:

```powershell
python generate_certificate.py
```

By default, it reads `inputs/template.png` and writes `certificate_output.jpg`
using a fresh unique certificate number, the example student, and duration.
The standalone command does not upload the image or create a Drive share link.
Use the approved Streamlit workflow to create recipient-only Drive links.
Override values or paths for another certificate:

```powershell
python generate_certificate.py `
  --student-name "Jane Doe" `
  --workshop-duration "1–3 August 2026" `
  --output outputs/jane_doe.jpg
```

The renderer uses the supplied template's measured placeholder positions,
scales them with the image dimensions, and reduces font size when a value
needs to fit its area.

## Tests

```powershell
python -m unittest discover -s tests
```
