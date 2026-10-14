import streamlit as st
from datetime import datetime

# Green Bharat - a simple pollution-reduction activity app
st.set_page_config(
    page_title="Green Bharat 🌱",
    page_icon="🌍",
    layout="centered"
)

# Session storage for this running app session
if "green_actions" not in st.session_state:
    st.session_state.green_actions = []

st.title("🌍 Green Bharat")
st.subheader("Small actions. A cleaner India. 🇮🇳")
st.write(
    "Upload a photo showing what you did to avoid pollution "
    "and inspire others to protect our planet."
)

st.info(
    "Ideas: plant a tree, walk or cycle instead of using a vehicle, "
    "reuse items, pick up litter, or avoid single-use plastic."
)

st.markdown("### 🌱 Share your green action")

with st.form("green_action_form"):
    name = st.text_input("Your name", placeholder="Enter your name")
    activity = st.selectbox(
        "What did you do?",
        [
            "Planted a tree or cared for a plant",
            "Walked or cycled instead of using a vehicle",
            "Collected litter or cleaned an area",
            "Avoided single-use plastic",
            "Reused or recycled something",
            "Saved electricity or water",
            "Used public transport or carpooled",
            "Other green action",
        ],
    )
    description = st.text_area(
        "Describe your action",
        placeholder="Tell us how your action helps the environment..."
    )
    photo = st.file_uploader(
        "Upload a photo of your action",
        type=["jpg", "jpeg", "png"],
        help="Choose a JPG or PNG image from your device."
    )
    submitted = st.form_submit_button("🌿 Submit My Green Action")

if submitted:
    if not name.strip():
        st.error("Please enter your name.")
    elif not description.strip():
        st.error("Please describe what you did.")
    elif photo is None:
        st.error("Please upload a photo of your green action.")
    else:
        # Keep the photo in session memory while this app session is running.
        image_bytes = photo.getvalue()
        st.session_state.green_actions.append(
            {
                "name": name.strip(),
                "activity": activity,
                "description": description.strip(),
                "image": image_bytes,
                "image_type": photo.type or "image/png",
                "submitted_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            }
        )
        st.success("Thank you! Your green action has been submitted. 💚")
        st.balloons()

st.divider()
st.markdown("### 🌏 Green Bharat Community")
st.metric("Green actions submitted this session", len(st.session_state.green_actions))

# Show submitted actions, newest first
for index, action in enumerate(reversed(st.session_state.green_actions), start=1):
    with st.container(border=True):
        st.markdown(f"**🌱 {action['name']}** — {action['activity']}")
        st.caption(f"Submitted: {action['submitted_at']}")
        st.write(action["description"])
        st.image(action["image"], caption="Community green action", use_container_width=True)

st.caption(
    "Demo note: submissions are kept only while this app session is running. "
    "For a public app, add secure permanent storage and moderation before launch."
)
