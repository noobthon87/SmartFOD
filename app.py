"""SmartFOD — AI-Powered Foreign Object Detection Assistant (Core MVP)."""
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from fod import records
from fod.pdf import build_clearance_pdf
from fod.vision import compare_images

load_dotenv()

# On Streamlit Community Cloud, the key lives in st.secrets rather than a .env file.
if not os.environ.get("ANTHROPIC_API_KEY"):
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

st.set_page_config(page_title="SmartFOD", page_icon="🛠️", layout="wide")

if "before_image" not in st.session_state:
    st.session_state.before_image = None
if "after_image" not in st.session_state:
    st.session_state.after_image = None
if "findings" not in st.session_state:
    st.session_state.findings = None

st.title("🛠️ SmartFOD")
st.caption("AI-Powered Foreign Object Detection Assistant")

page = st.sidebar.radio("Navigate", ["New Scan", "History"])

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.warning("ANTHROPIC_API_KEY is not set. Add it to your .env file before running a scan.")

if page == "New Scan":
    st.header("1. Job Details")
    col1, col2 = st.columns(2)
    with col1:
        job_card = st.text_input("Job Card Number")
    with col2:
        task_description = st.text_input("Task Description")

    st.header("2. Before Photo")
    before_file = st.camera_input("Photograph the work area BEFORE starting the task", key="before_cam")
    if before_file is None:
        before_file = st.file_uploader("...or upload a before photo", type=["jpg", "jpeg", "png"], key="before_upload")
    if before_file is not None:
        st.session_state.before_image = before_file.getvalue()
        st.image(st.session_state.before_image, caption="Before", width=300)

    st.header("3. After Photo")
    after_file = st.camera_input("Photograph the work area AFTER completing the task", key="after_cam")
    if after_file is None:
        after_file = st.file_uploader("...or upload an after photo", type=["jpg", "jpeg", "png"], key="after_upload")
    if after_file is not None:
        st.session_state.after_image = after_file.getvalue()
        st.image(st.session_state.after_image, caption="After", width=300)

    st.header("4. AI Comparison")
    run_disabled = not (st.session_state.before_image and st.session_state.after_image)
    if st.button("Run FOD Scan", disabled=run_disabled):
        with st.spinner("Analysing images with Claude..."):
            st.session_state.findings = compare_images(
                st.session_state.before_image, st.session_state.after_image
            )

    findings = st.session_state.findings
    if findings:
        if "error" in findings:
            st.error(findings["error"])
        else:
            if findings.get("clear"):
                st.success(f"CLEAR — {findings.get('summary', '')}")
            else:
                st.error(f"FLAGGED — {findings.get('summary', '')}")

            flagged_items = findings.get("flagged_items", [])
            if flagged_items:
                st.table(flagged_items)

            st.header("5. Sign Off")
            with st.form("sign_off_form"):
                technician = st.text_input("Technician Name")
                submitted = st.form_submit_button("Sign Off & Save Record")

            if submitted:
                if not job_card:
                    st.warning("Enter a job card number above before signing off.")
                elif not technician:
                    st.warning("Enter a technician name before signing off.")
                else:
                    before_path = records.save_image(st.session_state.before_image, "before")
                    after_path = records.save_image(st.session_state.after_image, "after")
                    record = records.add_record(
                        {
                            "job_card": job_card,
                            "task_description": task_description,
                            "technician": technician,
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                            "findings": findings,
                            "before_image": before_path,
                            "after_image": after_path,
                        }
                    )
                    st.session_state.last_record = record
                    st.success(f"Clearance record saved (ID: {record['id'][:8]}).")

    last_record = st.session_state.get("last_record")
    if last_record:
        pdf_bytes = build_clearance_pdf(
            last_record,
            os.path.join(records.DATA_DIR, last_record["before_image"]),
            os.path.join(records.DATA_DIR, last_record["after_image"]),
        )
        st.download_button(
            "Download Clearance Record (PDF)",
            data=pdf_bytes,
            file_name=f"fod_clearance_{last_record['job_card']}.pdf",
            mime="application/pdf",
        )

elif page == "History":
    st.header("Clearance Record History")
    all_records = list(reversed(records.load_records()))
    if not all_records:
        st.info("No clearance records yet.")
    for rec in all_records:
        status = "CLEAR" if rec.get("findings", {}).get("clear") else "FLAGGED"
        with st.expander(f"[{status}] Job Card {rec.get('job_card')} — {rec.get('timestamp')}"):
            st.write(f"**Task:** {rec.get('task_description')}")
            st.write(f"**Technician:** {rec.get('technician')}")
            st.write(f"**Summary:** {rec.get('findings', {}).get('summary')}")
            flagged = rec.get("findings", {}).get("flagged_items", [])
            if flagged:
                st.table(flagged)
            pdf_bytes = build_clearance_pdf(
                rec,
                os.path.join(records.DATA_DIR, rec["before_image"]),
                os.path.join(records.DATA_DIR, rec["after_image"]),
            )
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"fod_clearance_{rec.get('job_card')}.pdf",
                mime="application/pdf",
                key=f"dl_{rec['id']}",
            )
