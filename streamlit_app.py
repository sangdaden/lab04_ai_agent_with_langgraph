import uuid

import streamlit as st

from agent import run_agent

st.set_page_config(page_title="TravelBuddy", page_icon="✈️", layout="centered")

st.title("✈️ TravelBuddy")
st.caption("UI cơ bản cho trợ lý du lịch dùng LangGraph + checkpoint.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"streamlit-{uuid.uuid4()}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Xin chào! Mình là TravelBuddy. "
                "Bạn có thể hỏi về chuyến bay, khách sạn hoặc ngân sách du lịch."
            ),
        }
    ]


def reset_chat() -> None:
    st.session_state.thread_id = f"streamlit-{uuid.uuid4()}"
    st.session_state.pop("pending_prompt", None)
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Đã tạo cuộc trò chuyện mới. Bạn muốn đi đâu tiếp theo?",
        }
    ]


SUGGESTION_OPTIONS = [
    {
        "title": "🛫 Vé Hà Nội → Đà Nẵng",
        "description": "Xem các chuyến bay phổ biến.",
        "prompt": "Tìm vé từ Hà Nội đến Đà Nẵng",
    },
    {
        "title": "🏨 Hotel Phú Quốc",
        "description": "Khách sạn dưới 1 triệu/đêm.",
        "prompt": "Gợi ý khách sạn ở Phú Quốc dưới 1 triệu",
    },
    {
        "title": "💰 Tính ngân sách",
        "description": "Ước tính chuyến đi 2 ngày.",
        "prompt": "Tính ngân sách 5 triệu cho chuyến đi 2 ngày",
    },
]

with st.sidebar:
    st.subheader("⚙️ Tùy chọn & Gợi ý")
    st.write("Mỗi phiên chat dùng một `thread_id` riêng để giữ ngữ cảnh hội thoại.")
    st.code(st.session_state.thread_id, language="text")

    if st.button("🗑️ Xóa hội thoại", use_container_width=True):
        reset_chat()

    st.markdown("---")
    st.markdown("### 💡 Gợi ý nhanh")
    st.caption("Chọn nhanh một mẫu câu hỏi để gửi vào hội thoại.")

    for idx, option in enumerate(SUGGESTION_OPTIONS):
        with st.container(border=True):
            st.markdown(f"**{option['title']}**")
            st.caption(option["description"])
            if st.button("Chọn", key=f"suggestion_{idx}", use_container_width=True):
                st.session_state.pending_prompt = option["prompt"]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


typed_prompt = st.chat_input("Nhập yêu cầu du lịch của bạn...")
prompt = typed_prompt or st.session_state.pop("pending_prompt", None)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("TravelBuddy đang suy nghĩ..."):
            try:
                reply = run_agent(prompt, thread_id=st.session_state.thread_id)
            except Exception as exc:
                reply = f"Xin lỗi, hiện hệ thống đang gặp sự cố: `{exc}`"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
