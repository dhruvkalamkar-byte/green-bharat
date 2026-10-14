
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.set_page_config(page_title="Green Bharat", page_icon="🌱")

st.title("🌱 Green Bharat")
st.write("Share your actions to reduce pollution and protect our planet!")

# Connect to Supabase using Streamlit Secrets
try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SECRET_KEY"]
    )
except Exception:
    st.error("Database connection failed. Please check Streamlit Secrets.")
    st.stop()

st.subheader("📸 Share Your Green Action")

with st.form("green_action_form"):
    name = st.text_input("Your name")
    activity = st.selectbox(
        "What did you do?",
        [
            "Planted a tree",
            "Used public transport",
            "Walked or cycled",
            "Avoided plastic",
            "Recycled waste",
            "Saved electricity",
            "Cleaned my surroundings",
            "Other"
        ]
    )
    description = st.text_area("Describe your green action")
    photo = st.file_uploader(
        "Upload a photo as evidence",
        type=["jpg", "jpeg", "png"]
    )
    submitted = st.form_submit_button("Submit Green Action 🌍")

if submitted:
    if not name.strip() or not description.strip() or photo is None:
        st.warning("Please enter your name, description, and upload a photo.")
    else:
        try:
            image_bytes = photo.getvalue()
            extension = photo.name.rsplit(".", 1)[-1].lower()
            photo_path = f"{uuid.uuid4().hex}.{extension}"

            # Upload photo to private Supabase Storage
            supabase.storage.from_("green-photos").upload(
                photo_path,
                image_bytes,
                {"content-type": photo.type}
            )

            # Save the submission in the database
            supabase.table("green_actions").insert({
                "name": name.strip(),
                "activity": activity,
                "description": description.strip(),
                "photo_path": photo_path,
                "points": 0,
                "verification_status": "pending"
            }).execute()

            st.success(
                "Your green action was saved permanently! "
                "It is awaiting verification."
            )
        except Exception as error:
            st.error("Could not save your submission. Please try again.")
            st.caption("Check your Supabase table and storage bucket settings.")

st.divider()
st.subheader("🌿 Community Green Actions")
st.caption("Only approved submissions appear here.")

try:
    result = (
        supabase.table("green_actions")
        .select("*")
        .eq("verification_status", "approved")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )

    actions = result.data or []

    if not actions:
        st.info("No approved actions yet. Be the first to share one!")

    for action in actions:
        with st.container(border=True):
            st.write("### " + action["activity"])
            st.write(action["description"])
            st.caption("Shared by " + action["name"])
            st.caption(
                "Submitted: " + str(action.get("created_at", ""))
            )

            try:
                signed = supabase.storage.from_("green-photos").create_signed_url(
                    action["photo_path"], 3600
                )
                photo_url = signed.get("signedURL") or signed.get("signedUrl")
                if photo_url:
                    st.image(photo_url, width=400)
            except Exception:
                st.caption("Photo temporarily unavailable.")

except Exception:
    st.warning("Unable to load community actions right now.")

st.divider()
st.caption(
    "🌍 Green Bharat | All submissions start pending. "
    "Points are not awarded until actions are verified."
)
