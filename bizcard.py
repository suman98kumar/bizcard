from PIL import Image
import pytesseract
import pandas as pd
import numpy as np
import re
import io
import streamlit as st
import psycopg2
from psycopg2 import sql

# Set Tesseract executable path (update this path based on your Tesseract installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to extract text from an image using pytesseract
def image_to_text(path):
    try:
        # Load image
        input_img = Image.open(path)
        # Resize image to a reasonable size for processing
        input_img = input_img.resize((800, 600))

        # Use pytesseract to extract text
        text = pytesseract.image_to_string(input_img)

        return text, input_img
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Function to handle database operations
def perform_database_operations(concat_df, input_img):
    try:
        # CONNECTING WITH POSTGRESQL DATABASE
        connection_params = {
            'host': "localhost",
            'user': "postgres",
            'password': "Sugu1234",
            'database': "bizcard",
            'port': "5432",
        }

        with psycopg2.connect(**connection_params) as mydb:
            # Create a cursor
            mycursor = mydb.cursor()


            # Create table if not exists
            create_table_query = '''
            CREATE TABLE IF NOT EXISTS bizcard_details (
                NAME varchar(225),
                DESIGNATION varchar(225),
                COMPANY_NAME varchar(225),
                CONTACT varchar(225),
                EMAIL text,
                WEBSITE text,
                ADDRESS text,
                PINCODE varchar(225),
                Image text
            )'''
            mycursor.execute(create_table_query)
            mydb.commit()

            # Insert data into the table
            for index, row in concat_df.iterrows():
                insert_query = '''
                    INSERT INTO bizcard_details (NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, PINCODE, Image)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                values = (
                    row['NAME'], row['DESIGNATION'], row['COMPANY_NAME'], row['CONTACT'],
                    row['EMAIL'], row['WEBSITE'], row['ADDRESS'], row['PINCODE'], row['Image']
                )
                mycursor.execute(insert_query, values)
                mydb.commit()

            # Fetch data from the table
            query = 'SELECT * FROM bizcard_details'
            df_from_sql = pd.read_sql_query(query, mydb)

        return df_from_sql

    except psycopg2.Error as e:
        st.error(f"PostgreSQL error: {e}")
        return None

# Function to extract text details from OCR output using pytesseract
def extracted_text(text):
    extrd_dict = {"NAME": [], "DESIGNATION": [], "COMPANY_NAME": [], "CONTACT": [], "EMAIL": [],
                  "WEBSITE": [], "ADDRESS": [], "PINCODE": []}
    
    lines = text.split('\n')
    extrd_dict["NAME"].append(lines[0])
    extrd_dict["DESIGNATION"].append(lines[1])

    for i in range(2, len(lines)):
        if re.match(r'^[A-Za-z]', lines[i]):
            extrd_dict["COMPANY_NAME"].append(lines[i])
        elif lines[i].startswith("+") or (lines[i].replace("-", "").isdigit() and '-' in lines[i]):
            extrd_dict["CONTACT"].append(lines[i])
        elif "@" in lines[i] and ".com" in lines[i]:
            small = lines[i].lower()
            extrd_dict["EMAIL"].append(small)
        elif "WWW" in lines[i] or "www" in lines[i] or "Www" in lines[i] or "wWw" in lines[i] or "wwW" in lines[i]:
            small = lines[i].lower()
            extrd_dict["WEBSITE"].append(small)
        elif "Tamil Nadu" in lines[i] or "TamilNadu" in lines[i] or lines[i].isdigit():
            extrd_dict["PINCODE"].append(lines[i])
        elif re.match(r'^[A-Za-z]', lines[i]):
            extrd_dict["COMPANY_NAME"].append(lines[i])
        else:
            remove_colon = re.sub(r'[,;]', '', lines[i])
            extrd_dict["ADDRESS"].append(remove_colon)

    for key, value in extrd_dict.items():
        if len(value) > 0:
            concadenate = ' '.join(value)
            extrd_dict[key] = [concadenate]
        else:
            value = 'NA'
            extrd_dict[key] = [value]

    return extrd_dict

# Streamlit Part


# Set page configurations
st.set_page_config(
    page_title="Bizcard OCR App",
    page_icon="📇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
custom_styles = """
<style>
    body {
        background-color: #f2f2f2;
        font-family: 'Arial, sans-serif';
    }

    .sidebar .sidebar-content {
        background-color: #333333;
        color: white;
    }

    .title {
        font-size: 48px;
        font-weight: bold;
        color: #ffffff;
        background-color: #009688;
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    .menu-radio {
        color: #009688;
        font-size: 20px;
    }

    .upload-section {
        margin-top: 20px;
    }

    .process-image {
        margin-top: 20px;
    }

    .preview-section {
        margin-top: 20px;
    }

    .modify-section {
        margin-top: 20px;
    }

    .save-button {
        background-color: #009688;
        color: white;
        font-size: 16px;
        border-radius: 5px;
        margin-top: 20px;
    }

    .delete-section {
        margin-top: 20px;
    }

    .delete-button {
        background-color: #FF6347;
        color: white;
        font-size: 16px;
        border-radius: 5px;
        margin-top: 20px;
    }
</style>
"""

# Apply custom styles
st.markdown(custom_styles, unsafe_allow_html=True)

# Display the custom-styled title using Markdown
st.markdown("<div class='title'>EXTRACTING BUSINESS CARD DATA WITH 'OCR'</div>", unsafe_allow_html=True)

with st.sidebar:
    select = st.radio("Menu", ["Home", "Upload & Modifying", "Delete"], key="menu")

if select == "Home":
    st.markdown("### :blue[**Technologies Used :**] Python, Tesseract OCR, Streamlit, SQL, Pandas")
    st.write("### :blue[**About :**] Bizcard is a Python application designed to extract information from business cards.")
    st.write(
        '### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by Tesseract OCR through pytesseract, Bizcard is able to extract text from the images.')

elif select == "Upload & Modifying":
    img = st.file_uploader("Upload the Image (Max size: 10 MB)", type=["png", "jpg", "jpeg"], accept_multiple_files=False, key="file_uploader")

    if img is not None:
        st.image(img, width=300, caption="Uploaded Image")

        with st.spinner("Processing Image..."):
            text_image, input_img = image_to_text(img)
            text_dict = extracted_text(text_image)

        if text_dict:
            st.success("TEXT IS EXTRACTED SUCCESSFULLY")

    method = st.radio("Select the Option", ["None", "Preview", "Modify"], key="upload_method")

    if method == "None":
        st.write("")

    if method == "Preview":
        df = pd.DataFrame(text_dict)
        Image_bytes = io.BytesIO()

        # Convert image to bytes before saving
        if input_img is not None:
            input_img.convert('RGB').save(Image_bytes, format="PNG")

        image_data = Image_bytes.getvalue()
        data = {"Image": [image_data]}
        df_1 = pd.DataFrame(data)
        concat_df = pd.concat([df, df_1], axis=1)
        st.image(input_img, width=350, caption="Preview Image")
        st.dataframe(concat_df)

    if method == "Modify":
        col1, col2 = st.columns(2)
        df = pd.DataFrame(text_dict)
        Image_bytes = io.BytesIO()

        # Convert image to bytes before saving
        if input_img is not None:
            input_img.convert('RGB').save(Image_bytes, format="PNG")

        image_data = Image_bytes.getvalue()
        data = {"Image": [image_data]}
        df_1 = pd.DataFrame(data)
        concat_df = pd.concat([df, df_1], axis=1)

        with col1:
            modify_name = st.text_input("Name", text_dict["NAME"][0])
            modify_desig = st.text_input("Designation", text_dict["DESIGNATION"][0])
            modify_company = st.text_input("Company_Name", text_dict["COMPANY_NAME"][0])
            modify_contact = st.text_input("Contact", text_dict["CONTACT"][0])

            concat_df["NAME"] = modify_name
            concat_df["DESIGNATION"] = modify_desig
            concat_df["COMPANY_NAME"] = modify_company
            concat_df["CONTACT"] = modify_contact

        with col2:
            modify_email = st.text_input("Email", text_dict["EMAIL"][0])
            modify_web = st.text_input("Website", text_dict["WEBSITE"][0])
            modify_address = st.text_input("Address", text_dict["ADDRESS"][0])
            modify_pincode = st.text_input("Pincode", text_dict["PINCODE"][0])

            concat_df["EMAIL"] = modify_email
            concat_df["WEBSITE"] = modify_web
            concat_df["ADDRESS"] = modify_address
            concat_df["PINCODE"] = modify_pincode

        col1, col2 = st.columns(2)
        with col1:
            button3 = st.button("Save", use_container_width=True, key="save_button")

        if button3:
            df_from_sql = perform_database_operations(concat_df, input_img)

            if df_from_sql is not None and not df_from_sql.empty:
                st.dataframe(df_from_sql)
                st.success("Saved Successfully")

if select == "Delete":
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Sugu1234",
        database="bizcard",
        port="5432",
    )  # Connecting to PostgreSQL server

    mycursor = mydb.cursor()

    col1, col2 = st.columns(2)
    with col1:
        mycursor.execute("SELECT NAME FROM bizcard_details")
        mydb.commit()
        table1 = mycursor.fetchall()

        names = []

        for i in table1:
            names.append(i[0])

        name_select = st.selectbox("Select the Name", options=names)

    with col2:
        mycursor.execute(
            "SELECT DESIGNATION FROM bizcard_details WHERE NAME = %s", (name_select,)
        )
        mydb.commit()
        table2 = mycursor.fetchall()

        designations = []

        for j in table2:
            designations.append(j[0])

        designation_select = st.selectbox(
            "Select the Designation", options=designations
        )

    if name_select and designation_select:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"Selected Name: {name_select}")
            st.write("")
            st.write("")
            st.write(f"Selected Designation: {designation_select}")

        with col2:
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            remove = st.button("Delete", use_container_width=True, key="delete_button")

            if remove:
                try:
                    delete_query = "DELETE FROM bizcard_details WHERE NAME = %s AND DESIGNATION = %s"
                    delete_values = (name_select, designation_select)

                    mycursor.execute(delete_query, delete_values)
                    mydb.commit()

                    st.warning("Record Deleted Successfully")
                except psycopg2.Error as e:
                    st.error(f"PostgreSQL error: {e}")
