# Google Drive Integration Setup

This app can automatically upload generated certificates to Google Drive and generate public shareable links.

## Setup Steps (5 minutes)

### 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click the project dropdown (top-left) → **NEW PROJECT**
3. Enter name: `Certificate Generator`
4. Click **CREATE**

### 2. Enable Google Drive API

1. In the left menu, click **APIs & Services** → **Library**
2. Search for **Google Drive API**
3. Click it → **ENABLE**

### 3. Create OAuth2 Credentials

1. Go to **APIs & Services** → **Credentials** (left menu)
2. Click **+ CREATE CREDENTIALS** (top)
3. Select **OAuth client ID**
4. If prompted, click **Configure OAuth Consent Screen** first:
   - User Type: **External**
   - Fill in App Name: `Certificate Generator`
   - User Support Email: Your email
   - Developer Contact: Your email
   - Save and Continue
   - On Scopes screen, click **ADD OR REMOVE SCOPES**
   - Search for and add: `Google Drive API`
   - Save and Continue
   - Review and go back to Credentials

5. Back on Credentials page:
   - Click **+ CREATE CREDENTIALS** again
   - Select **OAuth client ID**
   - Application type: **Desktop app**
   - Name: `Certificate Generator`
   - Click **CREATE**

### 4. Download credentials.json

1. Click the download icon (↓) next to your OAuth client
2. Save as `credentials.json` in the **project root directory**
   
   ```
   certificate_generator_dreambot/
   ├── credentials.json        ← Place it here
   ├── certificate_generator/
   ├── main.py
   └── ...
   ```

**Important:** Never commit `credentials.json` to Git. It's already in `.gitignore`.

---

## How It Works

1. **First Run:** When the app generates certificates, it asks for Google permission (opens browser)
2. **Authentication:** A `token.pickle` file is saved locally (auto-refresh)
3. **Auto-Upload:** Each certificate is uploaded to a **DreambotCertificates** folder in your Google Drive
4. **Public Links:** Google Drive public links are automatically generated and included in:
   - Certificate previews
   - Email messages
   - Delivery report

---

## Verification

After first run, check your Google Drive:
- A folder named **DreambotCertificates** should appear
- Certificates are uploaded as `.jpg` files
- Folder is public (anyone with link can view)

---

## Troubleshooting

### "credentials.json not found"
- Download it from Google Cloud Console (see Step 4 above)
- Place it in the project root directory

### Browser doesn't open for authentication
- Copy the terminal link manually
- Paste in browser
- Grant permission
- Copy authorization code back to terminal

### "Permission denied" error
- Google Cloud Project may have incorrect permissions
- Re-check Step 2 (Google Drive API enabled)
- Delete `token.pickle` and re-run to re-authenticate

---

## Security Notes

- **credentials.json:** Gives access to your Google Drive; keep it private
- **token.pickle:** Auto-generated authentication token; keep it private
- **DreambotCertificates folder:** Public (anyone can download certificates with link)
- Both files are in `.gitignore` and never committed to GitHub

---

## Disabling Google Drive

If you don't want to use Google Drive:
- Remove `credentials.json`
- The app falls back to `APP_PUBLIC_URL` mode
- Certificates are served from the hosted app URL instead
