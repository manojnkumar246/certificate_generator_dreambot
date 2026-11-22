# Deployment Guide — Certificate Generator Streamlit App

This app generates, previews, and emails personalized internship certificates. For a **complete free deployment**, follow this guide.

---

## 🎯 Free Deployment Options

| Option | Storage | Email | Cost | Best For |
|--------|---------|-------|------|----------|
| **Railway + Gmail** | ✅ Persistent | ✅ SMTP 587 | FREE | Small batches, simple setup |
| **Render + SendGrid** | ✅ Persistent | ✅ Paid tier | ~$20/mo | Reliability & email volume |
| **Docker + Local VM** | ✅ Local disk | ✅ Your server | ⚠️ Setup | Full control, self-hosted |

**We recommend Railway** for easiest free setup. If you want truly cost-free, use the Docker + local VM approach.

---

## Option 1: Deploy on Railway (Recommended Free)

### Prerequisites
- GitHub account (fork or push this repo)
- Gmail account with app-specific password
- Railway account (free tier: $5 credit/month, enough for small batches)

### Step 1: Prepare Secrets

1. **Generate a Gmail App Password** (not your phone password):
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device)
   - Copy the 16-character password
   - Save it; you'll need it in Railway

2. **Generate Admin Password** for the hosted UI:
   - Use a random 16+ character string (e.g., `$(openssl rand -base64 16)`)
   - Or use any secure password you choose

### Step 2: Deploy on Railway

1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select this repository (`certificate_generator_dreambot`)
4. Railway auto-detects the Dockerfile ✓

### Step 3: Configure Environment Variables

In Railway dashboard, go to **Variables** and add:

```
APP_PASSWORD=your_gmail_app_password_here
APP_ADMIN_PASSWORD=your_admin_password_here
APP_PUBLIC_URL=https://certificate-generator-yourusername.railway.app
```

**Note:** Railway provides `RENDER_EXTERNAL_URL` automatically, but we set `APP_PUBLIC_URL` explicitly.

### Step 4: Deploy & Test

1. Click **"Deploy"**
2. Wait ~3–5 minutes for the build to complete
3. Railway shows your URL in the top-right corner
4. Visit it: `https://certificate-generator-yourusername.railway.app`
5. Log in with `APP_ADMIN_PASSWORD`

### Step 5: Generate & Send Certificates

1. Upload your `.xlsx` workbook with columns: **Name**, **Email**, **Send**, **Duration**
2. Click **"Generate certificate previews"**
3. Review each certificate preview
4. Check the **Approve & Send** checkbox for each student
5. Click **"Approve previews and send selected emails"**

**Important:** Certificates and their expiry registry are stored in Railway's persistent volume. Links work for 6 months after generation.

---

## Option 2: Deploy on Render (Free + Better Reliability)

Render offers a free tier but has limitations (see notes below).

### Prerequisites
- GitHub account
- Render account (free tier available)
- Gmail app password + admin password (same as Railway)

### Step 1–2: Setup Same as Railway

Same as Railway steps 1–2.

### Step 3: Create Render Service

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Select **"Deploy an existing repository"** → Choose this repo
4. Configuration:
   - **Name:** `certificate-generator`
   - **Environment:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run main.py --server.port=8501 --server.address=0.0.0.0`
   - **Plan:** Free (auto-spins down after 15 min inactivity)

### Step 4: Add Persistent Disk

Render's free plan loses files on restart. Add a persistent disk:

1. In Render dashboard, go to your service
2. **Disks** → **Add Disk**
   - **Mount Path:** `/app/outputs`
   - **Size:** 1 GB (free tier limit)

### Step 5: Environment Variables

Same as Railway:
```
APP_PASSWORD=your_gmail_app_password_here
APP_ADMIN_PASSWORD=your_admin_password_here
APP_PUBLIC_URL=https://certificate-generator-yourusername.onrender.com
```

### Step 6: Deploy

Click **"Create Web Service"** and wait for deployment.

**⚠️ Render Free Tier Limitations:**
- App spins down after 15 min inactivity (cold starts slow)
- SMTP port 587 may be blocked on free tier
- If email fails, upgrade to paid tier (~$7/mo for outbound SMTP)

---

## Option 3: Self-Hosted on Always-Free VM (Azure/GCP/AWS)

For complete control and zero cost, use a free tier VM.

### Prerequisites
- Azure/GCP/AWS account
- Local machine with Docker installed
- Domain name or static IP

### Step 1: Provision VM

**Azure (Always Free):**
```bash
# Create resource group
az group create --name cert-generator --location eastus

# Create B1s VM (1 vCPU, 1 GB RAM, free tier)
az vm create \
  --resource-group cert-generator \
  --name cert-gen-vm \
  --image UbuntuLTS \
  --size Standard_B1s \
  --admin-username azureuser \
  --generate-ssh-keys
```

### Step 2: SSH into VM and Install Docker

```bash
ssh azureuser@<your-vm-public-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
exit  # Reconnect to apply group changes
```

### Step 3: Clone & Deploy

```bash
git clone https://github.com/manojnkumar246/certificate_generator_dreambot.git
cd certificate_generator_dreambot

# Create .env.production with your secrets
cat > .env.production << EOF
APP_PASSWORD=your_gmail_app_password_here
APP_ADMIN_PASSWORD=your_admin_password_here
APP_PUBLIC_URL=https://your-vm-ip-or-domain.com
EOF

# Run with docker-compose
docker-compose up -d
```

### Step 4: Setup SSL (HTTPS)

Certificates require HTTPS. Use Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx -y

# If using Nginx as reverse proxy:
sudo certbot certonly --standalone -d your-domain.com
```

**Or use Caddy (auto-HTTPS):**
```bash
docker run -d -p 80:80 -p 443:443 \
  -v /path/to/outputs:/app/outputs \
  -e APP_PASSWORD=... \
  -e APP_ADMIN_PASSWORD=... \
  caddy reverse-proxy --from your-domain.com --to localhost:8501
```

### Step 5: Monitor & Logs

```bash
# View logs
docker-compose logs -f

# Check disk usage (certificates grow over time)
df -h

# Backup certificates periodically
sudo tar -czf backup-outputs.tar.gz /path/to/outputs
```

---

## 🔐 Security Checklist

- [ ] **Never commit `.env`** — Git already ignores it
- [ ] **Use strong `APP_ADMIN_PASSWORD`** — 16+ random characters
- [ ] **Rotate `APP_PASSWORD`** (Gmail) every 90 days
- [ ] **Use HTTPS only** — Set `APP_PUBLIC_URL=https://...`
- [ ] **Keep certificates private** — Expiry links are bearer tokens
- [ ] **Monitor storage usage** — Certificates accumulate in `outputs/`
- [ ] **Review delivery report** — Download after each batch

---

## Troubleshooting

### Certificates generate but emails don't send
1. Check `APP_PASSWORD` is set correctly (not your Gmail password, the app-specific one)
2. Check hosting provider allows outbound SMTP on port 587
   - **Railway:** ✅ Allowed
   - **Render Free:** ❌ Blocked (upgrade to paid or use SendGrid)
   - **Self-hosted VM:** ✅ Usually allowed

### Certificate links return "Expired"
- Expiry is 6 months from generation
- Regenerate the batch with the new `APP_PUBLIC_URL` after deployment

### App is slow to load
- **Railway/Render Free:** May have cold-start delays
- **Solution:** Use paid tier or keep app "warm" with periodic pings

### Storage is running out
- Certificates accumulate in `outputs/`
- Delete old batches: `outputs/<old-run-id>/` or implement cleanup

---

## Local Development (Before Deployment)

Test locally with Docker:

```bash
# Build image
docker build -t cert-gen .

# Run with environment file
docker run -d -p 8501:8501 \
  --env-file .env.sample \
  -v $(pwd)/outputs:/app/outputs \
  cert-gen

# Visit http://localhost:8501
```

---

## Questions?

Refer to the [main README](./README.md) for feature documentation.

For deployment-specific issues, check your hosting provider's docs or contact support.
