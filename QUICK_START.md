# Quick Start: Deploy Certificate Generator to Production

**TL;DR** — 5 minutes to live deployment on Railway (free tier):

## 1. Get Your Secrets

### Gmail App Password
1. Open https://myaccount.google.com/apppasswords
2. Select **Mail** → **Windows Computer** (or your device)
3. Google generates a 16-char password → **Copy it**
4. Save it somewhere safe (you'll paste it into Railway)

### Admin Password
Just make up a strong password (16+ chars). Examples:
- `P@ssw0rd!SecureAdmin123`
- Or generate one: https://www.random.org/passwords/

## 2. Deploy to Railway

1. **Fork this repo** (top-right: "Fork")
   - Or ensure your GitHub account has access to `manojnkumar246/certificate_generator_dreambot`

2. Go to **https://railway.app**
   - Sign up with GitHub (1 minute)
   - Click **"New Project"** → **"Deploy from GitHub"**
   - Search for `certificate_generator_dreambot`
   - Click **"Deploy"**

3. **Wait 2–3 minutes** for build to complete

4. Once deployed, Railway shows your URL (top-right corner):
   ```
   https://certificate-generator-yourusername.railway.app
   ```

## 3. Configure Secrets in Railway

In the Railway dashboard:

1. Click your project → **Variables**
2. Add three variables:

| Variable | Value |
|----------|-------|
| `APP_PASSWORD` | Paste your 16-char Gmail app password |
| `APP_ADMIN_PASSWORD` | Your admin password (e.g., `P@ssw0rd!SecureAdmin123`) |
| `APP_PUBLIC_URL` | `https://certificate-generator-yourusername.railway.app` |

3. Click **"Save"**
4. Railway redeploys automatically (~1 min)

## 4. Test It

1. Visit your URL: `https://certificate-generator-yourusername.railway.app`
2. Log in with `APP_ADMIN_PASSWORD`
3. Upload your `.xlsx` file (columns: **Name**, **Email**, **Send**, **Duration**)
4. Click **"Generate certificate previews"**
5. Review certificates
6. Click **"Approve & Send"**

✅ **Done!** Your app is live and sending emails.

---

## Need Help?

- **Gmail app password issues?** → See [Gmail Setup Guide](./DEPLOYMENT.md#step-1-prepare-secrets)
- **Email not sending?** → Check [Troubleshooting](./DEPLOYMENT.md#troubleshooting)
- **Want more control?** → Read [Full Deployment Guide](./DEPLOYMENT.md)
- **Self-hosted instead?** → See [Option 3: Self-Hosted VM](./DEPLOYMENT.md#option-3-self-hosted-on-always-free-vm)

---

## Important Notes

⚠️ **Never commit `.env`** — Git already ignores it.  
⚠️ **Keep `APP_ADMIN_PASSWORD` secret** — It protects your hosted UI.  
✅ **Certificates expire in 6 months** — Links stop working after that.  
✅ **Storage is persistent on Railway** — Certificates survive app restarts.

---

## Costs

**Railway Free Tier:**
- $5 credit/month
- Enough for ~100–200 certificates
- Exceeds that? Add a card; each GB costs ~$0.50/month
- **Most users stay free**

---

Happy certificate generating! 🎓
