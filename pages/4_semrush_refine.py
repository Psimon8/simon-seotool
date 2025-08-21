import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(
    layout="wide",
    page_title="Semrush Refine",
    page_icon="🥕"
)

# Helper function to categorize values
def get_category(position):
    if position == 1:
        return "Top 1"
    elif 2 <= position <= 3:
        return "Position 2-3"
    elif 4 <= position <= 5:
        return "Position 4-5"
    elif 6 <= position <= 10:
        return "Position 6-10"
    elif 11 <= position <= 20:
        return "Position 11-20"
    elif position >= 21:
        return "21+"
    return None

# Function to process the data
def process_data(data, regex_pattern):
    data['Category'] = data['Position'].apply(get_category)
    data['Marque/Hors Marque'] = data['Keyword'].apply(
        lambda x: "Marque" if re.search(regex_pattern, str(x), re.IGNORECASE) else "Hors Marque"
    )
    # Reorder columns: place Category and Marque/Hors Marque after Search Volume
    if "Search Volume" in data.columns:
        columns = list(data.columns)
        columns.insert(columns.index("Search Volume") + 1, columns.pop(columns.index("Category")))
        columns.insert(columns.index("Search Volume") + 2, columns.pop(columns.index("Marque/Hors Marque")))
        data = data[columns]

    # Group by Category and Marque/Hors Marque
    summary = data.groupby(['Category', 'Marque/Hors Marque']).size().unstack(fill_value=0)

    # Ensure the summary is displayed in the specified order
    category_order = ["Top 1", "Position 2-3", "Position 4-5", "Position 6-10", "Position 11-20", "21+"]
    summary = summary.reindex(category_order)

    return data, summary

# Export to Excel
def export_to_excel(df, summary):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Processed Data')
        summary.to_excel(writer, sheet_name='Summary')
    return output.getvalue()

# Streamlit UI
st.title("🥕 Semrush Refine")

# Create tabs
tab1, tab2 = st.tabs(["🚀 Main", "ℹ️ About"])

with tab1:
    # Step 1: Upload XLSX file
    uploaded_file = st.file_uploader("Upload your XLSX file", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        # Ensure necessary columns exist
        if "Keyword" in df.columns and "Position" in df.columns and "Search Volume" in df.columns:
            # Step 2: Input regex for "Marque"
            col1, col2 = st.columns(2)
            with col1:
                default_regex = re.escape(df['Keyword'].iloc[0].split('.')[0]).replace("\\", " ") if not df['Keyword'].empty else "..."
                regex_pattern = st.text_input("Enter regex pattern for 'Marque'", default_regex)
                selected_category = st.selectbox("Select Category", ["All"] + ["Top 1", "Position 2-3", "Position 4-5", "Position 6-10", "Position 11-20", "21+"])
                keyword = st.text_input("Enter Keyword (regex supported)")

            # Step 3: Process data
            processed_data, summary = process_data(df, regex_pattern)

            # Filter data based on selected category and keyword
            filtered_data = processed_data.copy()
            if selected_category != "All":
                filtered_data = filtered_data[filtered_data['Category'] == selected_category]
            if keyword:
                filtered_data = filtered_data[filtered_data['Keyword'].str.contains(keyword, case=False, na=False)]

            # Display summary table
            with col2:
                st.write("Summary Table:")
                summary_table = filtered_data.groupby(['Category', 'Marque/Hors Marque']).size().unstack(fill_value=0).reindex(["Top 1", "Position 2-3", "Position 4-5", "Position 6-10", "Position 11-20", "21+"], fill_value=0)
                st.dataframe(summary_table)

            # Display data for Marque and Hors Marque side by side
            col1, col2 = st.columns(2)
            with col1:
                st.write("Data for Marque:")
                marque_data = filtered_data[filtered_data['Marque/Hors Marque'] == 'Marque']
                st.dataframe(marque_data)
            with col2:
                st.write("Data for Hors Marque:")
                hors_marque_data = filtered_data[filtered_data['Marque/Hors Marque'] == 'Hors Marque']
                st.dataframe(hors_marque_data)

            # Step 5: Export processed data
            st.download_button(
                label="Download Processed Data",
                data=export_to_excel(filtered_data, summary),
                file_name="processed_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("The uploaded file must contain 'Keyword', 'Position', and 'Search Volume' columns.")

with tab2:
    st.markdown("## 📚 About Semrush Refine")
    
    st.markdown("""
    ### 🎯 What is Semrush Refine?
    
    Semrush Refine is a powerful tool designed to analyze and categorize SEO keyword data exported from Semrush. 
    It helps SEO professionals and digital marketers quickly identify brand vs non-brand keywords and understand 
    their position distribution across search results.
    """)
    
    st.markdown("""
    ### 📋 How to use this tool
    
    1. **Export your data from Semrush** as an Excel file (.xlsx)
    2. **Upload the file** using the file uploader
    3. **Configure the brand pattern** using regex to identify brand keywords
    4. **Filter and analyze** your data by category and keywords
    5. **Download the processed data** with new categorizations
    """)
    
    st.markdown("""
    ### 📊 Required Excel file format
    
    Your Semrush export must contain these columns:
    - **Keyword** : The search terms/keywords
    - **Position** : Current ranking position (1, 2, 3, etc.)
    - **Search Volume** : Monthly search volume for each keyword
    
    ⚠️ **Note:** The tool automatically detects these columns. Make sure your export includes them.
    """)
    
    st.markdown("""
    ### 🏷️ Categorization system
    
    The tool automatically categorizes your keywords into two dimensions:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 📍 Position Categories
        - **Top 1** : Position 1 (featured snippet territory)
        - **Position 2-3** : High visibility positions
        - **Position 4-5** : Above the fold positions
        - **Position 6-10** : First page positions
        - **Position 11-20** : Second page positions
        - **21+** : Lower ranking positions
        """)
    
    with col2:
        st.markdown("""
        #### 🎯 Brand Classification
        - **Marque** : Keywords containing your brand name
        - **Hors Marque** : Generic/non-brand keywords
        
        *Classification is based on the regex pattern you define*
        """)
    
    st.markdown("""
    ### 🔧 Brand Pattern Configuration
    
    The regex pattern helps identify brand-related keywords:
    
    - **Simple brand name** : `yourbrundname` (case-insensitive)
    - **Multiple variations** : `(brand|company|yourname)` 
    - **Exact match** : `^yourbrand$`
    - **With domain** : `yoursite\\.com`
    
    **Examples:**
    - For Nike: `nike` will match "nike shoes", "Nike running", etc.
    - For multiple brands: `(nike|adidas|puma)`
    """)
    
    st.markdown("""
    ### 📈 What you get
    
    **Summary Analysis:**
    - Cross-tabulation of position categories vs brand classification
    - Quick overview of your keyword distribution
    - Identify opportunities for improvement
    
    **Detailed Data:**
    - Original data with new categorization columns
    - Separate views for brand and non-brand keywords
    - Filtered results based on your selection criteria
    
    **Export Features:**
    - Download processed data as Excel file
    - Includes both detailed data and summary sheets
    - Ready for further analysis or reporting
    """)
    
    st.markdown("""
    ### 💡 Use cases
    
    - **Performance Analysis** : Compare brand vs non-brand keyword performance
    - **Content Strategy** : Identify gaps in non-brand keyword rankings
    - **Competitive Analysis** : Understand position distribution patterns
    - **Reporting** : Create categorized reports for stakeholders
    - **SEO Planning** : Prioritize optimization efforts by position categories
    """)
    
    st.info("""
    💡 **Pro Tip:** Use different regex patterns to segment your keywords by product lines, 
    services, or geographical locations for more granular analysis.
    """)

# Ajouter l'icône Twitter et le texte en bas à gauche
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