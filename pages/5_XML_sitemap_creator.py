import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from urllib.parse import urlparse
import io

st.set_page_config(
    page_title="XML Sitemap Generator",
    page_icon="🗺️",
    layout="wide"
)

def validate_url(url):
    """
    Validate that a URL is properly formatted.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except:
        return False

def create_sitemap_from_dataframe(df, changefreq="weekly", priority="0.8"):
    """
    Generate an XML sitemap from a pandas DataFrame.

    Args:
        df (pandas.DataFrame): DataFrame containing URLs in the first column
        changefreq (str): Frequency of page changes
        priority (str): Page priority
        
    Returns:
        tuple: (xml_string, valid_urls_count, skipped_urls_count)
    """
    urls = df.iloc[:, 0].tolist()
    
    # Create the root element <urlset>
    urlset_attributes = {
        "xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "xmlns:xhtml": "http://www.w3.org/1999/xhtml"
    }
    urlset = ET.Element("urlset", attrib=urlset_attributes)

    # Get the current date for <lastmod>
    current_date = datetime.now().astimezone().isoformat(timespec='seconds')

    valid_urls = 0
    skipped_urls = 0
    invalid_urls = []

    # For each URL, create a <url> element and its children
    for url_str in urls:
        if pd.isna(url_str) or not isinstance(url_str, str):
            skipped_urls += 1
            continue
            
        url_cleaned = url_str.strip()
        
        if not validate_url(url_cleaned):
            invalid_urls.append(url_str)
            skipped_urls += 1
            continue

        url_element = ET.SubElement(urlset, "url")
        
        loc_element = ET.SubElement(url_element, "loc")
        loc_element.text = url_cleaned
        
        lastmod_element = ET.SubElement(url_element, "lastmod")
        lastmod_element.text = current_date
        
        changefreq_element = ET.SubElement(url_element, "changefreq")
        changefreq_element.text = changefreq
        
        priority_element = ET.SubElement(url_element, "priority")
        priority_element.text = priority
        
        valid_urls += 1

    # Create an ElementTree object from the root element
    tree = ET.ElementTree(urlset)
    
    # Indentation for more readable XML
    ET.indent(tree, space="  ", level=0)

    # Convert to XML string
    xml_buffer = io.BytesIO()
    tree.write(xml_buffer, encoding='utf-8', xml_declaration=True)
    xml_string = xml_buffer.getvalue()
    
    return xml_string, valid_urls, skipped_urls, invalid_urls

def main():
    st.title("🗺️ XML Sitemap Generator")
    
    # Create tabs
    tab1, tab2 = st.tabs(["🚀 Main", "ℹ️ About"])
    
    with tab1:
        # Upload Excel file
        uploaded_file = st.file_uploader(
            "Choose your Excel file",
            type=['xlsx', 'xls'],
            help="The file must contain URLs in the first column"
        )
        
        # Sitemap configuration (always visible)
        st.markdown("### ⚙️ Sitemap Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            changefreq = st.selectbox(
                "Change frequency",
                ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"],
                index=3,  # "weekly" by default
                help="Indicates how frequently the page is likely to change"
            )
        
        with col2:
            priority = st.slider(
                "Priority",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                help="Relative priority of this URL compared to other URLs on your site"
            )
        
        if uploaded_file is not None:
            try:
                # Read the Excel file
                df = pd.read_excel(uploaded_file, header=None, usecols=[0])
                
                st.success(f"✅ File loaded successfully! {len(df)} lines detected.")
                
                # Show a preview of the data
                st.markdown("### 👀 URLs Preview")
                st.dataframe(
                    df.head(10),
                    column_config={
                        0: st.column_config.TextColumn("URLs")
                    },
                    use_container_width=True
                )
                
                if len(df) > 10:
                    st.info(f"Showing first 10 URLs out of {len(df)} total.")
                
                # Generate button
                if st.button("🚀 Generate Sitemap", type="primary", use_container_width=True):
                    with st.spinner("Generating sitemap..."):
                        xml_content, valid_urls, skipped_urls, invalid_urls = create_sitemap_from_dataframe(
                            df, changefreq, str(priority)
                        )
                    
                    # Show statistics
                    st.markdown("### 📊 Results")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Valid URLs", valid_urls, delta=None)
                    
                    with col2:
                        st.metric("Skipped URLs", skipped_urls, delta=None)
                    
                    with col3:
                        st.metric("File size", f"{len(xml_content)} bytes", delta=None)
                    
                    # Show invalid URLs if any
                    if invalid_urls:
                        with st.expander(f"⚠️ Invalid URLs ignored ({len(invalid_urls)})"):
                            for url in invalid_urls[:20]:  # Limit to 20 for display
                                st.text(url)
                            if len(invalid_urls) > 20:
                                st.info(f"... and {len(invalid_urls) - 20} other invalid URLs")
                    
                    # Download button
                    st.markdown("### 📥 Download")
                    
                    filename = f"sitemap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                    
                    st.download_button(
                        label="📥 Download XML Sitemap",
                        data=xml_content,
                        file_name=filename,
                        mime="application/xml",
                        type="primary",
                        use_container_width=True
                    )
                    
                    # Preview of the generated XML
                    with st.expander("👁️ Generated XML Preview"):
                        st.code(xml_content.decode('utf-8')[:2000] + "..." if len(xml_content) > 2000 else xml_content.decode('utf-8'), language="xml")
                    
                    st.success("✨ Sitemap generated successfully!")
            
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
        
        else:
            st.info("👆 Please upload an Excel file to get started.")
    
    with tab2:
        st.markdown("## 📚 Guidelines and Information")
        
        st.markdown("""
        ### 📋 Instructions
        1. **Upload** your Excel file (.xlsx or .xls)
        2. **Configure** sitemap parameters (optional)
        3. **Generate** and download your XML sitemap
        
        ⚠️ **Important:** URLs must be in the first column (A) of your Excel file.
        """)
        
        st.markdown("""
        ### 🎯 What is an XML sitemap?
        
        An XML sitemap is a file that lists the URLs of a website to inform search engines 
        about the site structure and facilitate indexing. It's a standardized protocol that helps Google, 
        Bing and other search engines discover and index your pages more efficiently.
        """)
        
        st.markdown("""
        ### 📋 Required format for your Excel file
        
        **Expected structure:**
        - 📄 **Format:** `.xlsx` or `.xls`
        - 📍 **Column A (first column):** One URL per line
        - ✅ **With or without headers** (doesn't matter)
        
        **Structure example:**
        ```
        | A                           |
        |-----------------------------|
        | https://mysite.com          |
        | https://mysite.com/about    |
        | https://mysite.com/contact  |
        | https://mysite.com/blog     |
        ```
        """)
        
        st.markdown("""
        ### 🔧 XML sitemap elements
        
        Each URL in the sitemap contains the following elements:
        
        - **`<loc>`** : Complete URL of the page (required)
        - **`<lastmod>`** : Last modification date (generated automatically)
        - **`<changefreq>`** : Estimated change frequency
        - **`<priority>`** : Relative priority from 0.0 to 1.0
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 🔄 Change frequencies
            
            - **always** : Changes on each visit
            - **hourly** : Changes every hour
            - **daily** : Changes every day
            - **weekly** : Changes every week *(recommended)*
            - **monthly** : Changes every month
            - **yearly** : Changes every year
            - **never** : Never changes
            """)
        
        with col2:
            st.markdown("""
            #### ⭐ Recommended priorities
            
            - **1.0** : Homepage
            - **0.8** : Important pages *(default)*
            - **0.6** : Category pages
            - **0.4** : Content pages
            - **0.2** : Archive pages
            - **0.1** : Less important pages
            """)
        
        st.markdown("""
        ### ✅ Accepted URL formats
        
        **Valid URLs:**
        - ✅ `https://example.com`
        - ✅ `http://example.com/page`
        - ✅ `https://subdomain.example.com/path/to/page`
        - ✅ `https://example.com/page?param=value`
        - ✅ `https://example.com/page#section`
        
        **URLs that will be ignored:**
        - ❌ `example.com` (without protocol)
        - ❌ `/page` (relative URL)
        - ❌ `www.example.com` (without protocol)
        - ❌ Empty or invalid cells
        """)
        
        st.markdown("""
        ### 🚀 Using the generated sitemap
        
        Once your XML sitemap is generated:
        
        1. **Download** the XML file
        2. **Upload it** to your website root
        3. **Submit it** in Google Search Console
        4. **Add** the sitemap URL to your robots.txt:
           ```
           Sitemap: https://your-site.com/sitemap.xml
           ```
        """)
        
        st.markdown("""
        ### 📊 Limits and best practices
        
        - **Maximum 50,000 URLs** per sitemap (Google limit)
        - **Maximum size:** 50 MB uncompressed
        - **Encoding:** UTF-8 required
        - **Updates:** Regular updates recommended
        - **Validation:** Test your sitemap with online tools
        """)
        
        st.info("""
        💡 **Tip:** Use this generator to create specialized sitemaps 
        (e.g.: sitemap for blog articles, sitemap for product pages, etc.)
        """)

if __name__ == "__main__":
    main()
