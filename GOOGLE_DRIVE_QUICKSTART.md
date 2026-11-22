# 🎓 Automatic Public URLs — Get Started in 10 Minutes

Your app now automatically generates **public Google Drive links** for certificates. No deployment needed!

---

## ⚡ 3-Step Quick Start

### Step 1: Setup Google Drive OAuth2 (5 minutes)

Follow [GOOGLE_DRIVE_SETUP.md](./GOOGLE_DRIVE_SETUP.md):

1. Create Google Cloud Project
2. Enable Google Drive API
3. Create OAuth2 credentials
4. Download `credentials.json` → Place in project root

Done! Google Drive is ready.

### Step 2: Run the App

```powershell
# Install dependencies (first time only)
python -m pip install -r requirements.txt

# Run the app
streamlit run main.py
```

Browser opens to `http://localhost:8501`

### Step 3: Generate Certificates with Public URLs

1. Upload your `.xlsx` file (columns: **Name**, **Email**, **Send**, **Duration**)
2. Click **"Generate certificate previews"**
3. ✨ **Certificates auto-upload to Google Drive**
4. 🔗 **Public URLs appear in preview** (click to verify)
5. Click **"Approve & Send"** to email
6. URLs are in the email and CSV report

---

## 📋 What Each Certificate Gets

| Item | Value |
|------|-------|
| **Certificate UID** | `DB-WS7-2026-UNIQUE_ID` |
| **Public URL** | `https://drive.google.com/uc?id=...` |
| **Status** | Public (anyone can download) |
| **Storage** | Google Drive (DreambotCertificates folder) |
| **Lifetime** | Permanent (hosted by Google) |

---

## 📧 Email Recipients Will See

Recipients get an email with:
- Attached certificate (`.jpg`)
- Link to view on Google Drive
- Certificate UID and verification info

---

## 📁 Google Drive Folder Structure

After first run, you'll see in your Google Drive:

```
📁 DreambotCertificates (Public - Anyone with link can view)
   ├── DB-WS7-2026-ABC123XYZ.jpg
   ├── DB-WS7-2026-DEF456UVW.jpg
   └── DB-WS7-2026-GHI789RST.jpg
```

**Share this folder link:**
```
https://drive.google.com/drive/folders/{FOLDER_ID}?usp=sharing
```

Recipients can download individual certificates or browse all.

---

## 🔧 Configuration

### `.env` File (Optional - for Email Sending)

If you want **email delivery**, add to `.env`:

```text
APP_PASSWORD=your_gmail_app_password
APP_ADMIN_PASSWORD=any_admin_password
```

Get Gmail app password:
1. https://myaccount.google.com/apppasswords
2. Select **Mail** → **Windows Computer**
3. Copy 16-char password → Paste in `.env`

**Without these**, the app still generates certificates and public URLs, just won't send emails.

---

## ✅ Verification Checklist

- [ ] `credentials.json` downloaded and placed in project root
- [ ] First run: Browser opened for OAuth2 permission
- [ ] `token.pickle` created (auto-saved)
- [ ] Google Drive shows "DreambotCertificates" folder
- [ ] Certificate preview shows public Google Drive URL
- [ ] Can click URL in preview to view certificate

---

## 🆘 Troubleshooting

### "credentials.json not found"
**Fix:** Follow step 1 of [GOOGLE_DRIVE_SETUP.md](./GOOGLE_DRIVE_SETUP.md) again

### "Browser doesn't open for auth"
**Fix:** Copy terminal link → Paste in browser → Grant permission → Copy code back

### "URLs not appearing in preview"
**Fix:** 
1. Check browser console for errors (F12)
2. Ensure `credentials.json` is in project root
3. Delete `token.pickle` and re-run to re-authenticate

### "Emails not sending"
**Fix:** Set `APP_PASSWORD` in `.env` (this is optional; certificates work without it)

---

## 📝 Notes

- ✅ **Certificates are permanent** (hosted by Google)
- ✅ **No expiry** (unlike deployed app mode)
- ✅ **Public by default** (anyone with link can view)
- ✅ **No app deployment needed**
- ⚠️ Never commit `credentials.json` or `token.pickle` (they're in `.gitignore`)

---

## 🎯 Workflow Summary

```
Your Computer                 Google Drive              Email
     ↓                              ↓                      ↓
1. Generate Certs --------→ Auto-upload Certificates ----→ Send Public Link
2. Preview URLs ←---------- Receive Public URLs ←--------
3. Approve & Send ------→ Certificates stay forever
```

---

## Done! 🎉

Your certificates now have **public, permanent URLs** automatically!

For more details, see:
- [README.md](./README.md) — Full feature documentation
- [GOOGLE_DRIVE_SETUP.md](./GOOGLE_DRIVE_SETUP.md) — OAuth2 detailed setup
- [DEPLOYMENT.md](./DEPLOYMENT.md) — Optional: Deploy the app itself
