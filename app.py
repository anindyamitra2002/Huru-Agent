import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime
import pytz

# Authentication credentials
auth = HTTPBasicAuth("admin", "aOt74B4j")

# API Endpoints
BASE_URL = "http://20.193.145.154/api"
START_CALL_URL = f"{BASE_URL}/start_call"
CALL_STATUS_URL = f"{BASE_URL}/call_status/{{call_sid}}"
ALL_CALLS_URL = f"{BASE_URL}/all_calls"

# Custom CSS for centered title and button styling
st.markdown("""
<style>
    /* Center the title */
    h1 {
        text-align: center;
    }
    
    /* Style for Dial Call button (Green when enabled) */
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #28a745;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Function to get call status
def get_call_status(call_sid):
    """
    Fetches the current status of a call using the call_sid.
    
    Args:
        call_sid (str): The unique identifier of the call.
        
    Returns:
        str or None: The call status if successful, None if the request fails.
    """
    url = CALL_STATUS_URL.format(call_sid=call_sid)
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()["status"]
    else:
        st.error("Failed to retrieve call status.")
        return None

# Function to get recent calls
def get_recent_calls(limit=10):
    """
    Fetches the most recent calls.
    
    Args:
        limit (int): The number of recent calls to fetch.
        
    Returns:
        list or None: A list of recent calls if successful, None if the request fails.
    """
    url = f"{ALL_CALLS_URL}?limit={limit}"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()["calls"]
    else:
        st.error("Failed to retrieve recent calls.")
        return None

# Function to convert UTC time to IST
def convert_to_ist(utc_time_str):
    """
    Convert UTC time string to IST time string.
    
    Args:
        utc_time_str (str): UTC time string.
        
    Returns:
        str: IST time string.
    """
    if not utc_time_str:
        return "-"
    try:
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S%z")
        ist_tz = pytz.timezone('Asia/Kolkata')
        ist_time = utc_time.astimezone(ist_tz)
        return ist_time.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return utc_time_str

# Streamlit app
st.title("Huru Customer Support")

# Initialize session state variables
if 'call_in_progress' not in st.session_state:
    st.session_state.call_in_progress = False
if 'call_sid' not in st.session_state:
    st.session_state.call_sid = None
if 'call_status' not in st.session_state:
    st.session_state.call_status = None

# Input field in one row (left-aligned)
to_number = st.text_input(
    "Receiver Number (including country code)",
    placeholder="+919876543210"
)

# Button in next row (left-aligned) - always enabled
dial_button = st.button(
    "Dial Call",
    key="dial_button"
)

# Dial Call logic
if dial_button:
    payload = {"to_number": to_number, "company": "huru"}
    response = requests.post(START_CALL_URL, json=payload, auth=auth)
    if response.status_code == 200:
        data = response.json()
        st.session_state.call_sid = data["call_sid"]
        st.session_state.call_in_progress = True
        st.session_state.call_status = "initiated"
        st.success("Call initiated successfully.")
    else:
        st.error("Failed to start the call. Please check the number and try again.")

# Display call status if a call is in progress
if st.session_state.call_in_progress and st.session_state.call_sid:
    status = get_call_status(st.session_state.call_sid)
    if status:
        st.session_state.call_status = status
        st.write(f"**Status:** {status}")
        if status in ["completed", "canceled"]:
            st.session_state.call_in_progress = False
            st.session_state.call_sid = None
            st.success("Call has ended.")

    if st.button("Refresh Status"):
        status = get_call_status(st.session_state.call_sid)
        if status:
            st.session_state.call_status = status
            st.info(f"Updated Call Status: {status}")
            if status in ["completed", "canceled"]:
                st.session_state.call_in_progress = False
                st.session_state.call_sid = None
                st.success("Call has ended.")

# Recent Calls section
st.markdown("### Recent Calls")
if st.button("Refresh Call History"):
    pass  # The table will refresh on rerun

recent_calls = get_recent_calls(limit=10)
if recent_calls:
    calls_data = []
    for call in recent_calls:
        calls_data.append({
            "Receiver": call.get("to", "-"),
            "Start Time (IST)": convert_to_ist(call.get("start_time", "-")),
            "End Time (IST)": convert_to_ist(call.get("end_time", "-")),
            "Duration (s)": call.get("duration_in_seconds", "0"),
            "Status": call.get("status", "-"),
            "Call ID": call.get("sid", "-")
        })
    df = pd.DataFrame(calls_data)
    st.dataframe(df, height=400)
else:
    st.info("No recent calls found or unable to retrieve call history.")