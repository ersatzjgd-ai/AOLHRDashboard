import streamlit as st
import pandas as pd
import requests

# --- APP CONFIGURATION ---
st.set_page_config(page_title="AOL HR", layout="wide", page_icon="💼")

# --- SECRETS MANAGEMENT ---
try:
    API_KEY = st.secrets["SERPAPI_KEY"]
except KeyError:
    st.error("Api config error.")
    st.stop()

# --- UI HEADER ---
st.title("💼 Internal Job Search Portal")
st.write("Search live job portals).")

# --- SIDEBAR: SEARCH PARAMETERS ---
st.sidebar.header("🔍 Search Parameters")

job_title = st.sidebar.text_input("Job Title / Keyword", placeholder="e.g., Senior Python Developer")
location = st.sidebar.text_input("Location", placeholder="e.g., Mumbai, Bangalore")

date_filter = st.sidebar.selectbox(
    "Date Posted",
    options=["Past 24 Hours (Today)"],
    index=0 
)

# Map UI selection to SerpApi's time parameter (tbs)
date_restrict_mapping = {
    "Past 24 Hours (Today)": "d",
    "Past Week": "w",
    "Any Time": None
}
selected_date = date_restrict_mapping[date_filter]

target_portals = st.sidebar.multiselect(
    "Target Job Boards",
    options=["instahyre.com", "naukri.com", "linkedin.com/jobs", "foundit.in"],
    default=["instahyre.com", "naukri.com"]
)

# --- SERPAPI FUNCTION ---
def fetch_jobs_from_serpapi(api_key, title, loc, portals, date_restrict):
    """Calls SerpApi to scrape Google search results and parse the data."""
    
    site_query = " OR ".join([f"site:{site}" for site in portals])
    search_query = f'"{title}" {loc} ({site_query})'
    
    url = "https://serpapi.com/search.json"
    
    params = {
        "engine": "google",
        "q": search_query,
        "api_key": api_key,
        "num": 20 # Number of results to fetch
    }
    
    if date_restrict:
        params["tbs"] = f"qdr:{date_restrict}"
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        st.error(f"API Error: {response.json().get('error', 'Unknown Error')}")
        return pd.DataFrame()
        
    data = response.json()
    items = data.get('organic_results', [])
    
    if not items:
        return pd.DataFrame()
        
    results = []
    for item in items:
        results.append({
            "Job Title / Post": item.get('title', '').replace(' | LinkedIn', '').replace(' - Naukri.com', ''),
            "Brief Description": item.get('snippet', ''),
            "Direct Link": item.get('link', ''),
            "Source": item.get('source', '')
        })
        
    return pd.DataFrame(results)

# --- MAIN DASHBOARD AREA ---
if st.button("Search Live Jobs", type="primary"):
    if not job_title:
        st.warning("Please enter a Job Title or Keyword to begin your search.")
    elif not target_portals:
        st.warning("Please select at least one Target Job Board.")
    else:
        with st.spinner(f"Querying search engines for '{job_title}' roles in '{location}' ({date_filter})..."):
            
            df_results = fetch_jobs_from_serpapi(
                API_KEY, 
                job_title, 
                location, 
                target_portals, 
                selected_date
            )
            
            if df_results.empty:
                st.warning(f"No results found posted in the {date_filter}. Try broadening your search terms.")
            else:
                st.success(f"Successfully retrieved {len(df_results)} postings!")
                
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
