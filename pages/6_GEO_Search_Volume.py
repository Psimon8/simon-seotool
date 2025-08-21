import streamlit as st
import pandas as pd
import requests
import json
import base64
from io import BytesIO
import time

st.set_page_config(
    page_title="GEO Search Volume",
    page_icon="📊",
    layout="wide"
)

def make_dataforseo_request(login, password, keywords, location_code=2840, language_code="en"):
    """
    Make request to DataforSEO API for search volume data
    """
    # Encode credentials
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    
    # Prepare request data according to DataforSEO documentation
    post_data = dict()
    post_data[0] = dict(
        language_name="English" if language_code == "en" else {
            "fr": "French",
            "de": "German", 
            "es": "Spanish",
            "it": "Italian",
            "ja": "Japanese"
        }.get(language_code, "English"),
        location_code=location_code,
        keywords=keywords
    )
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Correct API endpoint
        response = requests.post(
            'https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live',
            data=json.dumps(post_data),
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None

def process_api_response(response_data):
    """
    Process API response and create DataFrame
    """
    if not response_data or 'tasks' not in response_data:
        return None
    
    results = []
    for task in response_data['tasks']:
        if task['status_code'] == 20000 and 'result' in task:
            for result_item in task['result']:
                if 'items' in result_item:
                    for item in result_item['items']:
                        keyword_data = {
                            'Keyword': item.get('keyword', ''),
                            'Search Volume': item.get('ai_search_volume', 0),
                            'Competition': 0,  # Not available in this API
                            'CPC': 0,  # Not available in this API
                            'Monthly Searches': []
                        }
                        
                        # Add monthly search data if available
                        if 'ai_monthly_searches' in item and item['ai_monthly_searches']:
                            for month_data in item['ai_monthly_searches']:
                                keyword_data['Monthly Searches'].append({
                                    'year': month_data.get('year'),
                                    'month': month_data.get('month'),
                                    'search_volume': month_data.get('ai_search_volume')
                                })
                        
                        results.append(keyword_data)
        else:
            st.error(f"Task error - Status: {task.get('status_code')}, Message: {task.get('status_message', 'Unknown error')}")
    
    return pd.DataFrame(results) if results else None

def export_to_excel(df):
    """
    Export DataFrame to Excel format
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main data
        export_df = df.copy()
        if 'Monthly Searches' in export_df.columns:
            export_df = export_df.drop('Monthly Searches', axis=1)
        export_df.to_excel(writer, index=False, sheet_name='Search Volume Data')
        
        # Monthly trends if available
        if 'Monthly Searches' in df.columns and not df['Monthly Searches'].empty:
            trends_data = []
            for idx, row in df.iterrows():
                if row['Monthly Searches']:
                    for month_data in row['Monthly Searches']:
                        trends_data.append({
                            'Keyword': row['Keyword'],
                            'Year': month_data.get('year'),
                            'Month': month_data.get('month'),
                            'Search Volume': month_data.get('search_volume')
                        })
            
            if trends_data:
                trends_df = pd.DataFrame(trends_data)
                trends_df.to_excel(writer, index=False, sheet_name='Monthly Trends')
    
    return output.getvalue()

def main():
    st.title("📊 GEO Search Volume")
    
    # Create tabs
    tab1, tab2 = st.tabs(["🚀 Main", "ℹ️ About"])
    
    with tab1:
        # API Credentials section
        st.markdown("### 🔐 DataforSEO API Credentials")
        col1, col2 = st.columns(2)
        
        with col1:
            login = st.text_input("Login", type="default", help="Your DataforSEO login")
        
        with col2:
            password = st.text_input("Password", type="password", help="Your DataforSEO password")
        
        if not login or not password:
            st.warning("⚠️ Please enter your DataforSEO credentials to continue.")
            st.stop()
        
        # Location and language settings
        st.markdown("### 🌍 Location & Language Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            location_code = st.selectbox(
                "Location",
                [2840, 2826, 2250, 2276, 2724, 2380, 2392],
                format_func=lambda x: {
                    2840: "United States",
                    2826: "United Kingdom", 
                    2250: "France",
                    2276: "Germany",
                    2724: "Spain",
                    2380: "Italy",
                    2392: "Japan"
                }.get(x, str(x)),
                help="Select the target location for search volume data"
            )
        
        with col2:
            language_code = st.selectbox(
                "Language",
                ["en", "fr", "de", "es", "it", "ja"],
                format_func=lambda x: {
                    "en": "English",
                    "fr": "French",
                    "de": "German", 
                    "es": "Spanish",
                    "it": "Italian",
                    "ja": "Japanese"
                }.get(x, x),
                help="Select the target language"
            )
        
        # Keywords input section
        st.markdown("### 📝 Keywords Input")
        
        input_method = st.radio(
            "Choose input method:",
            ["Copy/Paste Keywords", "Upload Excel File"],
            horizontal=True
        )
        
        keywords = []
        
        if input_method == "Copy/Paste Keywords":
            keywords_text = st.text_area(
                "Enter keywords (one per line):",
                height=200,
                placeholder="keyword 1\nkeyword 2\nkeyword 3\n...",
                help="Enter each keyword on a new line"
            )
            
            if keywords_text:
                keywords = [kw.strip() for kw in keywords_text.split('\n') if kw.strip()]
                st.info(f"📊 {len(keywords)} keywords detected")
        
        else:  # Upload Excel File
            uploaded_file = st.file_uploader(
                "Upload Excel file with keywords",
                type=['xlsx', 'xls'],
                help="Keywords should be in the first column"
            )
            
            if uploaded_file:
                try:
                    df_upload = pd.read_excel(uploaded_file, header=None, usecols=[0])
                    keywords = [str(kw).strip() for kw in df_upload.iloc[:, 0].tolist() if pd.notna(kw) and str(kw).strip()]
                    st.success(f"✅ {len(keywords)} keywords loaded from file")
                    
                    # Show preview
                    st.markdown("**Keywords preview:**")
                    preview_df = pd.DataFrame({'Keywords': keywords[:10]})
                    st.dataframe(preview_df, use_container_width=True)
                    
                    if len(keywords) > 10:
                        st.info(f"Showing first 10 keywords out of {len(keywords)} total")
                        
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        
        # API Request section
        if keywords:
            st.markdown("### 🚀 Get Search Volume Data")
            
            # API limits warning
            st.warning(f"""
            ⚠️ **API Usage Notice:**
            - You're about to request data for {len(keywords)} keywords
            - DataforSEO charges per keyword processed
            - Make sure you have sufficient credits in your account
            """)
            
            if st.button("📊 Get Search Volume Data", type="primary", use_container_width=True):
                if len(keywords) > 1000:
                    st.error("Maximum 1000 keywords per request. Please reduce the number of keywords.")
                else:
                    with st.spinner(f"Fetching search volume data for {len(keywords)} keywords..."):
                        response_data = make_dataforseo_request(
                            login, password, keywords, location_code, language_code
                        )
                        
                        if response_data:
                            # Add debug expander
                            with st.expander("🐛 Debug - API Response (click to expand)"):
                                st.json(response_data)
                            
                            df_results = process_api_response(response_data)
                            
                            if df_results is not None and not df_results.empty:
                                st.success(f"✅ Successfully retrieved data for {len(df_results)} keywords!")
                                
                                # Display results
                                st.markdown("### 📊 Results")
                                
                                # Summary metrics
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("Total Keywords", len(df_results))
                                
                                with col2:
                                    avg_volume = df_results['Search Volume'].mean()
                                    st.metric("Avg Search Volume", f"{avg_volume:,.0f}")
                                
                                with col3:
                                    total_volume = df_results['Search Volume'].sum()
                                    st.metric("Total Search Volume", f"{total_volume:,.0f}")
                                
                                with col4:
                                    # Since CPC is not available in this API, show max volume instead
                                    max_volume = df_results['Search Volume'].max()
                                    st.metric("Max Search Volume", f"{max_volume:,.0f}")
                                
                                # Display data table
                                display_df = df_results.drop('Monthly Searches', axis=1) if 'Monthly Searches' in df_results.columns else df_results
                                # Remove CPC and Competition columns since they're not available
                                display_df = display_df[['Keyword', 'Search Volume']]
                                st.dataframe(display_df, use_container_width=True)
                                
                                # Export functionality
                                st.markdown("### 📥 Export Data")
                                
                                excel_data = export_to_excel(df_results)
                                filename = f"search_volume_data_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
                                
                                st.download_button(
                                    label="📥 Download Excel Report",
                                    data=excel_data,
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    type="primary",
                                    use_container_width=True
                                )
                                
                            else:
                                st.error("No data received from API. Please check your keywords and try again.")
                                # Show debug info when no data
                                if response_data:
                                    with st.expander("🐛 Debug - Full API Response"):
                                        st.json(response_data)

    with tab2:
        st.markdown("## 📚 About GEO Search Volume")
        
        st.markdown("""
        ### 🎯 What is GEO Search Volume?
        
        GEO Search Volume is a tool that retrieves accurate search volume data and trends for keywords 
        using the DataforSEO API. It provides comprehensive insights into keyword performance across 
        different geographical locations and languages.
        """)
        
        st.markdown("""
        ### 📋 How to use this tool
        
        1. **Enter your DataforSEO credentials** (login and password)
        2. **Select target location and language** for your analysis
        3. **Input keywords** either by copy/paste or Excel upload
        4. **Get search volume data** with a single click
        5. **Export results** to Excel for further analysis
        """)
        
        st.markdown("""
        ### 🔐 DataforSEO API Setup
        
        To use this tool, you need:
        - **DataforSEO account** ([Sign up here](https://dataforseo.com/))
        - **API credentials** (login and password)
        - **Sufficient credits** in your account
        
        ⚠️ **Important:** DataforSEO charges per keyword processed. Make sure you have enough credits before making requests.
        """)
        
        st.markdown("""
        ### 📊 Data provided
        
        For each keyword, you'll get:
        - **Search Volume** : Monthly average search volume
        - **Competition** : Competition level (0-1 scale)
        - **CPC** : Cost per click in USD
        - **Monthly Trends** : 12-month search volume history (when available)
        """)
        
        st.markdown("""
        ### 🌍 Supported locations
        
        The tool supports major markets including:
        - **United States** (2840)
        - **United Kingdom** (2826)
        - **France** (2250)
        - **Germany** (2276)
        - **Spain** (2724)
        - **Italy** (2380)
        - **Japan** (2392)
        
        *More locations available via DataforSEO API documentation*
        """)
        
        st.markdown("""
        ### 📝 Input methods
        
        **Copy/Paste Method:**
        - Enter keywords one per line
        - Maximum 1000 keywords per request
        - Ideal for quick analysis
        
        **Excel Upload Method:**
        - Upload .xlsx or .xls files
        - Keywords should be in the first column (A)
        - Headers are automatically handled
        """)
        
        st.markdown("""
        ### 📥 Export features
        
        **Excel Export includes:**
        - **Main sheet** : All keyword data with search volume, competition, and CPC
        - **Trends sheet** : Monthly search volume data (when available)
        - **Timestamp** : File includes generation timestamp
        """)
        
        st.markdown("""
        ### 💡 Use cases
        
        - **Keyword Research** : Validate keyword opportunities
        - **Content Planning** : Prioritize content based on search volume
        - **PPC Campaigns** : Get CPC estimates for ad budgeting
        - **Market Analysis** : Compare keyword performance across regions
        - **Trend Analysis** : Understand seasonal search patterns
        """)
        
        st.info("""
        💡 **Pro Tip:** Start with a small batch of keywords to test your API setup before processing large lists.
        """)
        
        st.markdown("""
        ### 🔗 Useful links
        
        - [DataforSEO API Documentation](https://docs.dataforseo.com/)
        - [DataforSEO Pricing](https://dataforseo.com/pricing)
        - [Location Codes](https://docs.dataforseo.com/v3/appendix/locations/)
        - [Language Codes](https://docs.dataforseo.com/v3/appendix/languages/)
        """)

if __name__ == "__main__":
    main()

# Add social links in sidebar
st.sidebar.markdown(
    """
    <div style="position: fixed; bottom: 10px; left: 20px;">
        <a href="https://github.com/Psimon8" target="_blank" style="text-decoration: none;">
            <img src="https://github.githubassets.com/assets/pinned-octocat-093da3e6fa40.svg" 
                 alt="GitHub Simon le Coz" style="width:20px; vertical-align: middle; margin-right: 5px;">
            <span style="color: white; font-size: 14px;"></span>
        </a>    
        <a href="https://www.linkedin.com/in/simon-le-coz/" target="_blank" style="text-decoration: none;">
            <img src="https://static.licdn.com/aero-v1/sc/h/8s162nmbcnfkg7a0k8nq9wwqo" 
                 alt="LinkedIn Simon Le Coz" style="width:20px; vertical-align: middle; margin-right: 5px;">
            <span style="color: white; font-size: 14px;"></span>
        </a>
        <a href="https://twitter.com/lekoz_simon" target="_blank" style="text-decoration: none;">
            <img src="https://abs.twimg.com/favicons/twitter.3.ico" 
                 alt="Twitter Simon Le Coz" style="width:20px; vertical-align: middle; margin-right: 5px;">
            <span style="color: white; font-size: 14px;">@lekoz_simon</span>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
