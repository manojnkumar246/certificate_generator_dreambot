# Certificate Generator with Google Drive Integration

A Streamlit application that creates personalized internship certificates from an Excel roster, **automatically uploads to Google Drive**, and emails certificates to recipients.

## 🆕 New Feature: Automatic Google Drive Upload

Generated certificates are **automatically uploaded to Google Drive** and given **public shareable links**. No app deployment needed!

**How it works:**
1. Generate certificates locally
2. Certificates auto-upload to your Google Drive folder
3. Public URLs are generated automatically
4. URLs are used in emails and delivery reports
5. Anyone with the link can download the certificate

---

## Project Layout

```text
certificate_generator/
  certificates.py           Certificate image generation
  emailing.py              Gmail SMTP connection and email composition
  processing.py            Batch previews, UIDs, expiry, and delivery report
  personalize_template.py  Pillow certificate renderer
  google_drive.py          🆕 Google Drive upload and link generation
  create_sample_excel.py
inputs/
  template.png             Default certificate artwork
  signature.png            Source signature artwork
outputs/                   Local backup copies of generated certificates
tests/
main.py                    Streamlit entry point
generate_certificate.py    Standalone single-certificate command
pyproject.toml
requirements.txt
credentials.json           🆕 Google OAuth2 credentials (not committed)
token.pickle              🆕 Auto-generated auth token (not committed)
GOOGLE_DRIVE_SETUP.md     🆕 Google Drive OAuth2 setup guide
```

---

## Setup and Run

### 1. Install Dependencies

Use Python 3.10 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Configure Google Drive (Optional but Recommended)

For automatic public certificate links without deploying an app:

1. Follow [GOOGLE_DRIVE_SETUP.md](./GOOGLE_DRIVE_SETUP.md) (~5 minutes)
2. Place `credentials.json` in the project root
3. Done! Certificates will auto-upload on first run

### 3. Configure Gmail (For Email Sending)

Add this entry to `.env` without quotes:

```text
APP_PASSWORD=your_gmail_app_password
APP_ADMIN_PASSWORD=your_admin_password
```

Get your Gmail app password:
1. Go to https://myaccount.google.com/apppasswords
2. Select **Mail** → **Windows Computer** (or your device)
3. Google generates a 16-char password → Copy it
4. Paste it in `.env`

### 4. Run the App

```powershell
streamlit run main.py
```

Then:
1. Upload an `.xlsx` workbook with columns: **Name**, **Email**, **Send**, **Duration**
2. Click **"Generate certificate previews"**
3. Review each preview
4. Certificates are auto-uploaded to Google Drive (if set up)
5. Click **"Approve & Send"** to email
6. Download the recipient report (`.csv`)

---

## ✨ Features

✅ **Google Drive Integration:** Auto-upload and generate public links  
✅ **Certificate Generation:** Personalized from template image  
✅ **Email Delivery:** Gmail SMTP with certificate attachment  
✅ **Preview & Approval:** Review before sending  
✅ **Delivery Report:** CSV tracking all sending results  
✅ **Expiry Registry:** 6-month link expiration (if using deployed app)  
✅ **CLI:** Standalone `generate_certificate.py` for single certificates  

---

## Usage

### Upload Student Data

The `.xlsx` file should have these columns (case-insensitive):
- **Name** (or `student_name`)
- **Email** (or `student_email`)
- **Send** (or `send_email`) — Use `yes` to request email delivery
- **Duration** (or `workshop_duration`) — Workshop date/period

Example:
```
Name           Email              Send  Duration
Alice Example  alice@example.com  yes   1–3 August 2026
Bob Example    bob@example.com    no    1–3 August 2026
```

### Generate Certificate

Use the standalone script for a single certificate:

```powershell
python generate_certificate.py `
  --student-name "Jane Doe" `
  --workshop-duration "1–3 August 2026" `
  --output outputs/jane_doe.jpg
```

---

## Deployment Options

If you want a **live hosted app** (optional):

- **Railway:** Easiest free tier (~5 min setup) — See [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Render:** Alternative free tier
- **Self-hosted:** Use always-free VM (Azure/GCP/AWS)

**Note:** Google Drive integration works **without deployment**. You can generate and share certificates entirely from your computer.

---

## Tests

```powershell
python -m unittest discover -s tests
```

---

## Security Notes

⚠️ **Never commit these files:**
- `.env` — Contains Gmail app password
- `credentials.json` — Google OAuth2 credentials
- `token.pickle` — Google authentication token

✅ All are in `.gitignore` by default.

---

## Troubleshooting

### "Certificate not uploading to Google Drive"
→ Check [GOOGLE_DRIVE_SETUP.md](./GOOGLE_DRIVE_SETUP.md) for OAuth2 setup

### "Email not sending"
→ Ensure `APP_PASSWORD` is set in `.env` (use Gmail app password, not phone password)

### "Google Drive folder is private"
→ Check folder permissions in Google Drive (should be "Anyone with link can view")

---

## Questions?

Refer to individual guides:
- **Google Drive:** [GOOGLE_DRIVE_SETUP.md](./GOOGLE_DRIVE_SETUP.md)
- **Deployment:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Quick Start:** [QUICK_START.md](./QUICK_START.md)
