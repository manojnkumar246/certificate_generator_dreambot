"""
============================================================================
  Dreambot Internship Certificate Generator
  ------------------------------------------
  A Streamlit web application that automates:
    1. Generating personalized certificates from a template image
    2. Emailing certificates to students via SMTP
    3. Providing a ZIP download of all generated certificates

  Author : Gowtham
  Date   : 2026-09-23
============================================================================
"""

from pathlib import Path
import hashlib
import hmac

import pandas as pd
import streamlit as st
from streamlit.runtime import exists as streamlit_runtime_exists

from certificate_generator.processing import (
    PreviewBatch,
    generate_previews,
    load_certificate_record,
    normalize_student_columns,
    send_approved_emails,
)
from certificate_generator.settings import (
    SENDER_EMAIL,
    get_app_admin_password,
    get_public_app_url,
    get_smtp_app_password,
)

if not streamlit_runtime_exists():
    raise SystemExit(
        "This app must be started by Streamlit. Run: python -m streamlit run main.py"
    )

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_ROOT / "inputs"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# ──────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Certificate Generator | Dreambot",
    page_icon="🎓",
    layout="centered",
)

certificate_uid = str(st.query_params.get("c", "")).strip()
if certificate_uid:
    try:
        certificate_record, certificate_path = load_certificate_record(
            OUTPUT_DIR,
            certificate_uid,
        )
    except TimeoutError as error:
        st.error(str(error))
        st.stop()
    except FileNotFoundError as error:
        st.error(str(error))
        st.stop()
    except OSError as error:
        st.error(f"Could not load this certificate: {error}")
        st.stop()

    st.title("Certificate verification")
    st.warning(
        "Anyone with this unique link can view the certificate until its "
        "expiry date. Do not post or forward the link publicly."
    )
    st.write(f"**Certificate UID:** `{certificate_record['certificate_uid']}`")
    st.write(f"**Recipient:** {certificate_record['name']}")
    st.write(f"**Expires:** {certificate_record['expires_at']}")
    st.image(certificate_path, width="stretch")
    st.download_button(
        "Download certificate",
        data=certificate_path.read_bytes(),
        file_name=f"{certificate_uid}.jpg",
        mime="image/jpeg",
        width="stretch",
    )
    st.stop()

if get_public_app_url() is not None:
    admin_password = get_app_admin_password()
    if not admin_password:
        st.error(
            "The public app is not configured safely. Set APP_ADMIN_PASSWORD "
            "in the hosting provider's secret settings."
        )
        st.stop()
    if not st.session_state.get("admin_authenticated", False):
        st.title("Certificate Generator")
        with st.form("admin_login"):
            entered_password = st.text_input(
                "Administrator password",
                type="password",
            )
            login_submitted = st.form_submit_button("Sign in")
        if login_submitted:
            if hmac.compare_digest(entered_password, admin_password):
                st.session_state["admin_authenticated"] = True
                st.rerun()
            st.error("Incorrect administrator password.")
        st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS for Premium Styling
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Main container ── */
    .main .block-container {
        max-width: 780px;
        padding-top: 2rem;
    }

    /* ── Header banner ── */
    .header-banner {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .header-banner h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        letter-spacing: 0.5px;
    }
    .header-banner p {
        color: #94a3b8;
        font-size: 1rem;
        margin: 0;
    }

    /* ── Section cards ── */
    .section-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Status messages ── */
    .status-success {
        padding: 0.5rem 1rem;
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        border-radius: 0 8px 8px 0;
        margin: 0.3rem 0;
        font-size: 0.9rem;
        color: #166534;
    }
    .status-skip {
        padding: 0.5rem 1rem;
        background: #fefce8;
        border-left: 4px solid #eab308;
        border-radius: 0 8px 8px 0;
        margin: 0.3rem 0;
        font-size: 0.9rem;
        color: #854d0e;
    }
    .status-error {
        padding: 0.5rem 1rem;
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        border-radius: 0 8px 8px 0;
        margin: 0.3rem 0;
        font-size: 0.9rem;
        color: #991b1b;
    }
    .status-info {
        padding: 0.5rem 1rem;
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        border-radius: 0 8px 8px 0;
        margin: 0.3rem 0;
        font-size: 0.9rem;
        color: #1e40af;
    }

    /* ── Summary card ── */
    .summary-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
        border-radius: 12px;
        padding: 1.5rem 2rem;
        color: white;
        text-align: center;
        margin: 1.5rem 0;
    }
    .summary-card h3 { margin: 0 0 1rem 0; font-weight: 600; }
    .summary-stats {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
    }
    .stat-item { text-align: center; }
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        display: block;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ── Hide default Streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* ── Button styling ── */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
    <h1>🎓 Certificate Generator</h1>
    <p>Generate • Preview • Approve • Email</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: Load Font
# ──────────────────────────────────────────────────────────────────────────────
def save_uploaded_asset(uploaded_file, target_name: str) -> Path:
    """Store a selected artwork file in the project's inputs directory."""
    target_path = INPUT_DIR / target_name
    target_path.write_bytes(uploaded_file.getvalue())
    return target_path


# STREAMLIT UI
# ══════════════════════════════════════════════════════════════════════════════

# ── Section 2: Upload Excel ──────────────────────────────────────────────────
st.markdown("""
<div class="section-card">
    <div class="section-title">📄 Upload Student Data</div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload Excel File (.xlsx)",
    type=["xlsx"],
    help=(
        "Excel file with columns: **Name**, **Email**, **Send** (yes/no), "
        "and **Duration**."
    ),
)

# Show a preview of the uploaded data
if uploaded_file is not None:
    try:
        df_preview = normalize_student_columns(pd.read_excel(uploaded_file))
        uploaded_file.seek(0)

        st.markdown("##### 📋 Data Preview")
        st.dataframe(
            df_preview,
            width="stretch",
            hide_index=True,
        )
        st.caption(f"📊 {len(df_preview)} student(s) found in file.")
    except (ValueError, OSError, ImportError) as e:
        st.error(f"❌ Could not read Excel file: {e}")
        st.stop()


# ── Section 3: Template Files Check ──────────────────────────────────────────
st.markdown("""
<div class="section-card">
    <div class="section-title">🖼️ Template Assets</div>
</div>
""", unsafe_allow_html=True)

# The provided template contains the fields used by the personalized renderer.
TEMPLATE_PATH = INPUT_DIR / "template.png"

uploaded_template = st.file_uploader(
    "Upload Template Image (optional)",
    type=["jpg", "jpeg", "png"],
    help="The uploaded template is saved under inputs/ for this project.",
)

if uploaded_template is not None:
    TEMPLATE_PATH = save_uploaded_asset(uploaded_template, "template.png")

if TEMPLATE_PATH.is_file():
    st.success(f"✅ Template found: `{TEMPLATE_PATH.name}`")
else:
    st.error("❌ Template image not found. Upload one or add inputs/template.png.")

# Section 4: Generate and approve previews
st.markdown("---")

if uploaded_file is not None and TEMPLATE_PATH.is_file():
    uploaded_file.seek(0)
    fingerprint = hashlib.sha256(
        uploaded_file.getvalue() + TEMPLATE_PATH.read_bytes()
    ).hexdigest()
    uploaded_file.seek(0)
else:
    fingerprint = ""

saved_fingerprint = st.session_state.get("preview_fingerprint")
if saved_fingerprint and saved_fingerprint != fingerprint:
    st.session_state.pop("preview_batch", None)
    st.session_state.pop("preview_fingerprint", None)

generate_btn = st.button(
    "Generate certificate previews (does not send email)",
    type="primary",
    width="stretch",
)

if generate_btn:
    errors = []
    if uploaded_file is None:
        errors.append("Please upload an Excel file.")
    if not TEMPLATE_PATH or not Path(TEMPLATE_PATH).is_file():
        errors.append("Template file not found. Upload one or add inputs/template.png.")

    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    uploaded_file.seek(0)
    students = normalize_student_columns(pd.read_excel(uploaded_file))
    if students.empty:
        st.error("The uploaded workbook does not contain any students.")
        st.stop()

    try:
        with st.spinner("Generating previews only. No emails will be sent yet..."):
            preview_batch = generate_previews(
                students=students,
                template_path=TEMPLATE_PATH,
                output_root=OUTPUT_DIR,
            )
    except (OSError, ValueError) as error:
        st.error(
            f"Could not generate previews: {error}"
        )
        st.stop()
    st.session_state["preview_batch"] = preview_batch
    st.session_state["preview_fingerprint"] = fingerprint

preview_batch = st.session_state.get("preview_batch")
if isinstance(preview_batch, PreviewBatch):
    st.markdown("### Review every certificate before sending")
    st.caption(
        "No email is sent until you approve the previews below and click "
        "**Approve previews and send selected emails**."
    )
    requested_records = [
        record
        for record in preview_batch.records
        if record["send_requested"] == "yes"
        and record["certificate_status"] == "generated"
    ]
    approvals = []
    for record in preview_batch.records:
        st.markdown(f"#### {record['name'] or '(missing name)'}")
        st.write(f"**Certificate UID:** `{record['certificate_uid']}`")
        st.write(f"**Duration:** {record['duration'] or '(missing duration)'}")
        st.write(f"**Recipient:** {record['email'] or '(missing email)'}")
        st.write(f"**Expires:** {record['expires_at']}")
        st.write(
            "**Certificate link:** "
            f"{record['verification_url'] or '(public app URL not configured)'}"
        )
        certificate_path = preview_batch.certificate_paths.get(
            record["certificate_uid"]
        )
        if certificate_path is not None:
            st.image(certificate_path, width=650)
            if record["send_requested"] == "yes":
                approvals.append(
                    st.checkbox(
                        f"I approve this preview for {record['name']} "
                        f"({record['certificate_uid']})",
                        key=f"approve_{record['certificate_uid']}",
                    )
                )
        else:
            st.error(record["error"])
        st.markdown("---")

    if not preview_batch.has_public_url and requested_records:
        st.warning(
            "No public app URL is configured. This batch can only use local "
            "preview links; set APP_PUBLIC_URL after deployment and generate "
            "a new batch before sending certificates."
        )

    pending_records = [
        record
        for record in requested_records
        if record["email_status"] == "pending_approval"
    ]
    all_previews_approved = len(approvals) == len(requested_records) and all(approvals)
    if pending_records:
        send_button = st.button(
            "Approve previews and send selected emails",
            type="primary",
            width="stretch",
            disabled=(
                not all_previews_approved
                or not preview_batch.has_public_url
            ),
        )
        if not preview_batch.has_public_url:
            st.info(
                "Email sending stays disabled until the public app URL is "
                "configured and this batch has public links."
            )
        if send_button:
            try:
                password = get_smtp_app_password()
                send_approved_emails(
                    preview_batch,
                    sender_email=SENDER_EMAIL,
                    email_password=password,
                )
                st.success("Approved email processing is complete.")
            except (OSError, ValueError) as error:
                st.error(f"Could not send approved emails: {error}")

    st.markdown("### Batch report")
    st.write(
        f"Generated: {preview_batch.generated_count} · "
        f"Accepted by SMTP: {preview_batch.emailed_count} · "
        f"Skipped: {preview_batch.skipped_count} · "
        f"Errors: {preview_batch.error_count}"
    )
    st.dataframe(
        pd.DataFrame(preview_batch.records),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        f"Run files: {preview_batch.output_dir.relative_to(PROJECT_ROOT)}"
    )
    st.download_button(
        label="Download all certificates (.zip)",
        data=preview_batch.archive_path.read_bytes(),
        file_name="certificates.zip",
        mime="application/zip",
        width="stretch",
    )
    st.download_button(
        label="Download recipient report (.csv)",
        data=preview_batch.report_path.read_bytes(),
        file_name="delivery_report.csv",
        mime="text/csv",
        width="stretch",
    )


# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 1rem 0;">
        Built with ❤️ using Streamlit &nbsp;|&nbsp; Dreambot Pvt Ltd &nbsp;|&nbsp; 2026
    </div>
    """,
    unsafe_allow_html=True,
)
