import streamlit as st
import pandas as pd
import requests

# --- APP CONFIGURATION ---
st.set_page_config(page_title="HR Sourcing Dashboard", layout="wide", page_icon="💼")

# --- SECRETS MANAGEMENT ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    CX_ID = st.secrets["GOOGLE_CX"]
except KeyError:
    st.error("🚨 API Keys are missing! Please configure 'GOOGLE_API_KEY' and 'GOOGLE_CX' in your hosting environment.")
    st.stop()

# --- UI HEADER ---
st.title("💼 Live Job Sourcing Dashboard")
st.write("Search live job portals using the Google Custom Search API.")

# --- SIDEBAR: SEARCH PARAMETERS ---
st.sidebar.header("🔍 Search Parameters")

job_title = st.sidebar.text_input("Job Title / Keyword", placeholder="e.g., Senior Python Developer")
location = st.sidebar.text_input("Location", placeholder="e.g., Bengaluru, Remote")

# NEW: Date restriction filter defaulting to Today
date_filter = st.sidebar.selectbox(
    "Date Posted",
    options=["Past 24 Hours (Today)", "Past Week", "Any Time"],
    index=0 
)

# Map UI selection to Google's specific dateRestrict syntax
date_restrict_mapping = {
    "Past 24 Hours (Today)": "d1",
    "Past Week": "w1",
    "Any Time": None
}
selected_date = date_restrict_mapping[date_filter]

target_portals = st.sidebar.multiselect(
    "Target Job Boards",
    options=["instahyre.com", "naukri.com", "linkedin.com/jobs", "foundit.in"],
    default=["instahyre.com", "naukri.com"]
)

# --- GOOGLE SEARCH API FUNCTION ---
def fetch_jobs_from_google(api_key, cx, title, loc, portals, date_restrict):
    """Calls the Google Custom Search API and parses the results."""
    
    site_query = " OR ".join([f"site:{site}" for site in portals])
    search_query = f'"{title}" {loc} ({site_query})'
    
    url = "https://www.googleapis.com/customsearch/v1"
    
    # Base parameters
    params = {
        'key': api_key,
        'cx': cx,
        'q': search_query,
        'num': 10 
    }
    
    # NEW: Dynamically inject the date filter if one is selected
    if date_restrict:
        params['dateRestrict'] = date_restrict
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        st.error(f"API Error: {response.json().get('error', {}).get('message', 'Unknown Error')}")
        return pd.DataFrame()
        
    data = response.json()
    items = data.get('items', [])
    
    if not items:
        return pd.DataFrame()
        
    results = []
    for item in items:
        results.append({
            "Job Title / Post": item.get('title', '').replace(' | LinkedIn', '').replace(' - Naukri.com', ''),
            "Brief Description": item.get('snippet', ''),
            "Direct Link": item.get('link', ''),
            "Source": item.get('displayLink', '')
        })
        
    return pd.DataFrame(results)

# --- MAIN DASHBOARD AREA ---
if st.button("Search Live Jobs", type="primary"):
    if not job_title:
        st.warning("Please enter a Job Title or Keyword to begin your search.")
    elif not target_portals:
        st.warning("Please select at least one Target Job Board.")
    else:
        with st.spinner(f"Querying Google for '{job_title}' roles in '{location}' ({date_filter})..."):
            
            # Pass the new selected_date parameter into our function
            df_results = fetch_jobs_from_google(
                API_KEY, 
                CX_ID, 
                job_title, 
                location, 
                target_portals, 
                selected_date
            )
            
            if df_results.empty:
                st.warning(f"No results found posted in the {date_filter}. Try broadening your search terms or expanding the date range.")
            else:
                st.success(f"Successfully retrieved {len(df_results)} postings from {date_filter}!")
                
                st.dataframe(
                    df_results,
                    column_config={
                        "Direct Link": st.column_config.LinkColumn("Apply / View Link")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                csv = df_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Results to CSV",
                    data=csv,
                    file_name='live_hr_sourcing_results.csv',
                    mime='text/csv',
                )
