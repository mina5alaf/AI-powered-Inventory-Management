
from transformers import pipeline
import json
import streamlit as st
import requests
import pandas as pd
import numpy as np
from streamlit_tags import st_tags  # to add labels on the fly!
import os
import re
import string

def load_data():
    with open('inventory.json') as json_file:
        data = json.load(json_file)
    return data

def save_data(data):
    with open('inventory.json', 'w') as json_file:
        json.dump(data, json_file)

def search_by_id(item_id):
    data = load_data()
    item = next((x for x in data if x['id'] == item_id), None)
    if item is None:
        print ("INVAAAAAALID")
        item = "Invlaid ID"
        return item
    
    return item
        
def update_item_loc(item_id,new_loc):
    data = load_data()
    item = next((x for x in data if x['id'] == item_id), None)
    if item is None:
        return "No Product found, Enter a valid item ID"
    old_loc = item["location"]
    item["location"] = new_loc
    
    save_data(data)
    return old_loc 

def adjust(item_id, qty, person):
    data = load_data()
    item = next((x for x in data if x['id'] == item_id), None)
    if item is None:
        return "No Product found, Enter a valid item ID"
    
    item["quantity"] = int(int(item["quantity"]) - int(qty))
    item["person"] = person
    
    save_data(data)
    return item

def dispose(item_id, qty):
    data = load_data()
    item = next((x for x in data if x['id'] == item_id ), None)
    if item is None:
        return "No Product found, Enter a valid item ID"
    
    item["quantity"] = int(int(item["quantity"]) - int(qty))
    
    save_data(data)
    return item


def update_item_quantity(item_id, qty, loc):
    data = load_data()
    item = next((x for x in data if (x['id'] == item_id and x['location'] == loc)), None)
    if item is None:
        return "No Product found, Enter a valid item ID"
    
    item["quantity"] = int(int(item["quantity"]) - int(qty))
    
    save_data(data)
    return item

def move_print(label, id, old_loc, new_loc):
    return {"Transaction Name": label,
            "Stock number": id,
            "Location from": old_loc,
            "Location to": new_loc}
    

st.set_page_config(
    layout="centered", page_title="Inventory Management", page_icon="❄️"
)



c1, c2 = st.columns([0.32, 2])

with c2:
    st.caption("")
    st.title("AI-powered Transaction Interpreter for Inventory Management")


if not "valid_inputs_received" in st.session_state:
    st.session_state["valid_inputs_received"] = False


############ SIDEBAR CONTENT ############

st.sidebar.write("")

# For elements to be displayed in the sidebar, we need to add the sidebar element in the widget.

# We create a text input field for users to enter their API key.
mine = "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"
API_KEY = st.sidebar.text_input(
    "Enter your HuggingFace API key",
    value="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",
    help="Once you created your HuggingFace account, you can get your free API token in your settings page: https://huggingface.co/settings/tokens",
    type="password",
)

os.environ["API_TOKEN"]=API_KEY

labels = ["Move Transaction", "Adjust Transaction", "Dispose Transaction", "Receive Transaction"]
API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
headers = {"Authorization": f"Bearer {API_KEY}"}


st.sidebar.markdown("---")


# Then, we create a intro text for the app, which we wrap in a st.markdown() widget.

st.write("")
st.markdown(
    """


"""
)

st.write("")

CommandTab, DisplayTab = st.tabs(["Write Command", "Data Display"])

with DisplayTab:
    with st.form(key="search"):
        search_text = st.text_area(
            "Search by ID",
            height=10,
            help="e.x. A004, leave empty to display all the data",
            key="2",
        )
        submit_button_disp = st.form_submit_button(label="Submit")

        if submit_button_disp and not search_text:
            data = load_data()
            df = pd.DataFrame(data)
            st.write(df)
            
        elif submit_button_disp and search_text:
            st.write(search_by_id(search_text))

with CommandTab:
    with st.form(key="my_form"):


        MAX_KEY_PHRASES = 50

        new_line = "\n"

        keyphrases_string = "I want to change location for item A001 to location Master."

        text = st.text_area(
            "Enter your command",
            keyphrases_string,
            height=50,
            help="Transactional text command",
            key="1",
        )

        submit_button = st.form_submit_button(label="Submit")

    if not submit_button and not st.session_state.valid_inputs_received:
            st.stop()

    elif submit_button and not text:
        st.warning("There is no command")
        st.session_state.valid_inputs_received = False
        st.stop()

    elif submit_button and text and not API_KEY:
        st.warning("Please enter your API Key")
        st.session_state.valid_inputs_received = False
        st.stop()

        
    elif submit_button or st.session_state.valid_inputs_received:

        if submit_button:
            st.session_state.valid_inputs_received = True

        def query(payload,API_URL):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()
        
        sentiment_output = query(
                    {
                        "inputs": {
                        "source_sentence": text,
                        "sentences": labels
                        },
                        "options": {"wait_for_model": True},
                    },API_URL
                )
        
        
        pos_output = query( {
        "inputs": text,
    },"https://api-inference.huggingface.co/models/TweebankNLP/bertweet-tb2_ewt-pos-tagging")

        #st.write(labels[np.array(api_json_output).argmax()])
        #st.write(pos_output)
        
        if labels[np.array(sentiment_output).argmax()] == "Move Transaction":
            item_loc = text.split("item ",1)
            item = item_loc[1]
            id = item.split(" ")[0]
            
            new_loc = item.split("location")[1].split(" ")[1]
            new_loc = new_loc.replace(".","")
            old_loc = update_item_loc(id, new_loc)
            st.write(move_print(labels[np.array(sentiment_output).argmax()], id, old_loc, new_loc))
            
        elif labels[np.array(sentiment_output).argmax()] == "Receive Transaction":
            item_loc = text.split("item ",1)
            item = item_loc[1]
            id = item.split(" ")[0]
            
            new_loc = item.split("location")[1].split(" ")[1]
            new_loc = new_loc.replace(".","")
            qty = re.findall(r'\d+',text)[0]
            st.write(f"Transaction Name: {labels[np.array(sentiment_output).argmax()]}")
            st.write(update_item_quantity(id, qty, new_loc))


        elif labels[np.array(sentiment_output).argmax()] == "Dispose Transaction":
            item_loc = text.split("item ",1)
            item = item_loc[1]
            id = item.split(" ")[0]
            
            qty = re.findall(r'\d+',text)[0]
            
            st.write(f"Transaction Name: {labels[np.array(sentiment_output).argmax()]}")
            st.write(dispose(id, qty))
        
        #Adjust transaction
        else:
            item_loc = text.split("item ",1)
            item = item_loc[1]
            id = item.split(" ")[0]
            
            qty = re.findall(r'\d+',text)[1]
            
            person = item.split("person")[1].split(" ")[1]
            person = person.replace(".","")
            
            st.write(adjust(id, qty, person))