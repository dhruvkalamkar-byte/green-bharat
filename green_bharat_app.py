

import streamlit as st
from supabase import create_client
from openai import OpenAI
import base64
import uuid
import hmac

st.set_page_config(page_title="Green Bharat", page_icon="🌱")

st.title("🌱 Green Bharat")
st.subheader("Small actions. A cleaner India. 🇮🇳")

# Connect to services

# Connect to services safely
required = [
    "SUPABASE_URL",
    "SUPABASE_SECRET_KEY",
    "OPENAI_API_KEY",
]

missing = [key for key in required if not st.secrets.get(key)]

if missing:
    st.error("Missing Streamlit Secrets: " + ", ".join(missing))
    st.stop()

try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SECRET_KEY"]
    )
    st.success("Supabase client setup passed.")
except Exception as e:
    st.error("Supabase setup failed.")
    st.caption("Error type: " + type(e).__name__)
    st.stop()

try:
    ai_client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )
    st.success("OpenAI client setup passed.")
except Exception as e:
    st.error("OpenAI setup failed.")
    st.caption("Error type: " + type(e).__name__)
    st.stop()



def review_photo(image_bytes, mime_type, activity, description):
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    response = ai_client.responses.create(
        model="gpt-4o-mini",
        input=[{
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Assess whether this photo appears relevant to "
                        "the claimed environmental action. Do not claim "
                        "that the photo proves the action happened. "
                        "State what is visible and any uncertainty.\n"
                        f"Activity: {activity}\nDescription: {description}"
                    )
                },
                {
                    "type": "input_image",
                    "image_url": (
                        f"data:{mime_type};base64,{encoded}"
                    ),
                    "detail": "low"
                }
            ]
        }],
        max_output_tokens=180
    )
    return response.output_text.strip()


def get_photo_url(path):
    result = supabase.storage.from_("green-photos").create_signed_url(
        path, 3600
    )
    return result.get("signedURL") or result.get("signedUrl")


# ---------------- Submission form ----------------

st.header("📸 Share Your Green Action")

with st.form("green_action_form"):
    name = st.text_input("Your name")
    activity = st.selectbox("What did you do?", [
        "Planted a tree",
        "Used public transport",
        "Walked or cycled",
        "Avoided plastic",
        "Recycled waste",
        "Saved electricity",
        "Cleaned my surroundings",
        "Other"
    ])
    description = st.text_area("Describe your green action")
    photo = st.file_uploader(
        "Upload a photo", type=["jpg", "jpeg", "png"]
    )
    submitted = st.form_submit_button("Submit Green Action 🌍")

if submitted:
    if not name.strip() or not description.strip() or photo is None:
        st.warning("Please complete all fields and upload a photo.")
    elif len(photo.getvalue()) > 5 * 1024 * 1024:
        st.warning("Please upload a photo smaller than 5 MB.")
    else:
        image_bytes = photo.getvalue()
        mime = photo.type
        if mime not in ("image/jpeg", "image/png"):
            st.error("Please use a JPG or PNG image.")
        else:
            extension = "jpg" if mime == "image/jpeg" else "png"
            path = f"{uuid.uuid4().hex}.{extension}"

            try:
                supabase.storage.from_("green-photos").upload(
                    path, image_bytes,
                    {"content-type": mime, "upsert": "false"}
                )
            except Exception:
                st.error("Photo upload failed. Check Supabase Storage.")
                st.stop()

            try:
                with st.spinner("AI is reviewing your photo..."):
                    ai_review = review_photo(
                        image_bytes, mime, activity, description.strip()
                    )
            except Exception:
                ai_review = "AI review unavailable. Human review required."

            try:
                supabase.table("green_actions").insert({
                    "name": name.strip(),
                    "activity": activity,
                    "description": description.strip(),
                    "photo_path": path,
                    "points": 0,
                    "verification_status": "pending",
                    "ai_review": ai_review
                }).execute()

                st.success("Your green action has been saved!")
                st.info("Status: Pending admin review.")
                st.write("**AI Photo Review:**", ai_review)
            except Exception:
                st.error(
                    "The photo may have uploaded, but the record failed "
                    "to save. Check Supabase before submitting again."
                )

# ---------------- Community feed ----------------

st.divider()
st.header("🌿 Approved Community Actions")

try:
    result = (
        supabase.table("green_actions")
        .select("*")
        .eq("verification_status", "approved")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )

    if not result.data:
        st.info("No approved actions yet. Be the first to share one!")

    for action in result.data or []:
        with st.container(border=True):
            st.subheader(action["activity"])
            st.write(action["description"])
            st.caption(f"Shared by {action['name']}")
            st.write(f"🏆 Points: {action.get('points', 0)}")
            try:
                st.image(get_photo_url(action["photo_path"]), width=350)
            except Exception:
                st.caption("Photo temporarily unavailable.")
except Exception:
    st.warning("Unable to load community actions.")

# ---------------- Admin approval panel ----------------

st.divider()
st.header("🔐 Admin Panel")

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    with st.form("admin_login"):
        password = st.text_input("Admin password", type="password")
        login = st.form_submit_button("Log in")

    if login:
        expected = st.secrets.get("ADMIN_PASSWORD", "")
        if expected and hmac.compare_digest(password, expected):
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("Incorrect password or ADMIN_PASSWORD not configured.")

if st.session_state.admin_logged_in:
    if st.button("Log out"):
        st.session_state.admin_logged_in = False
        st.rerun()

    st.subheader("Pending submissions")

    try:
        pending = (
            supabase.table("green_actions")
            .select("*")
            .eq("verification_status", "pending")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )

        if not pending.data:
            st.info("No pending submissions.")

        for action in pending.data or []:
            with st.container(border=True):
                st.subheader(action["activity"])
                st.write("**Submitted by:**", action["name"])
                st.write(action["description"])
                st.write("**AI review:**", action.get("ai_review") or "Not available")

                try:
                    st.image(get_photo_url(action["photo_path"]), width=350)
                except Exception:
                    st.warning("Could not load this photo.")

                points = st.number_input(
                    f"Points for submission {action['id']}",
                    min_value=0,
                    max_value=100,
                    value=10,
                    key=f"points_{action['id']}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Approve", key=f"approve_{action['id']}"):
                        updated = supabase.table("green_actions").update({
                            "verification_status": "approved",
                            "points": int(points)
                        }).eq("id", action["id"]).eq(
                            "verification_status", "pending"
                        ).execute()

                        if updated.data:
                            st.success("Submission approved!")
                            st.rerun()
                        else:
                            st.warning("No record updated. Refresh and check its status.")

                with col2:
                    if st.button("❌ Reject", key=f"reject_{action['id']}"):
                        updated = supabase.table("green_actions").update({
                            "verification_status": "rejected",
                            "points": 0
                        }).eq("id", action["id"]).eq(
                            "verification_status", "pending"
                        ).execute()

                        if updated.data:
                            st.success("Submission rejected.")
                            st.rerun()
                        else:
                            st.warning("No record updated. Refresh and check its status.")

    except Exception:
        st.error("Unable to load pending submissions. Check database access.")

st.caption(
    "🌍 Green Bharat | AI feedback is advisory. "
    "Human review is required before approval."
)
