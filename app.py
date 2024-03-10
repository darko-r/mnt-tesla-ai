import streamlit as st
import time
from openai import OpenAI
from helper import all_assistants, json_entry_list, classifier_prompt, condition_parse_prompt, classify, parse_condition
import re
import sys
import json

st.title("Simple chat")
client = OpenAI()
user_thread = client.beta.threads.create()

@st.cache_data
def load_assistants():
    return all_assistants()

@st.cache_data
def load_json_entry_list(path):
    return json_entry_list(path)

@st.cache_data
def load_asst_summary(path):
    return json.load(open(path))

json_entry_list_ = load_json_entry_list('metadata.json')
asst_summary = load_asst_summary('assistant_summary.json')

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("What is up?")
if prompt:
    response = None
    thread_message = client.beta.threads.messages.create(
        thread_id = user_thread.id,
        role = "user",
        content = prompt,
    )
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    class_ = classify(prompt)
    # class_ = "search"
    print(f"Classified: {prompt} as class: {class_}")
    if class_.lower() == "logic":
        conditions = parse_condition(prompt)
        print(f"Parsed prompt: {prompt} as condition: {conditions}")
        if "count" in conditions.lower():
            cnt = json_entry_list_.count(conditions[6:-1])
            response = "Count output not available :("
        else:
            return_list = json_entry_list_.fetch(conditions)
            response = f"Of course, here is a list of found documents that match your description: \n{', '.join(map(str, return_list)) }" if return_list else "Sorry, no documents match your description."
    elif class_.lower() == "summarize":
        title = prompt.lower().split('"')[1::2][0]
        print(f"looking for {title} summary")
        ret = [d for d in json_entry_list_.list_ if d.dict_['title'].lower() == title]
        if ret:
            ret = ret[0].dict_["assistant_OAI_id"]
            summary = [a_s for a_s in asst_summary if a_s['assistant_id'] == ret]
            response = summary[0]['summary']
        else:
            response = "Was not able to find the file specified :("
    else:
        file_assistants = load_assistants()
        for assistant in (a.id for a in file_assistants):
            print(f"Starting search for assistant {assistant}")
            run = client.beta.threads.runs.create(
                thread_id = user_thread.id,
                assistant_id = assistant
            )
            run = client.beta.threads.runs.retrieve(
                thread_id=user_thread.id,
                run_id=run.id
            )

            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(
                    thread_id=user_thread.id,
                    run_id=run.id
                )
                time.sleep(1)
            
            messages = client.beta.threads.messages.list(thread_id=user_thread.id)
            last_msg = max(messages.data, key = lambda x: x.created_at)
            assistant_response = re.sub('【.*】', '', last_msg.content[0].text.value)
            if assistant_response != "I'm sorry, I don't know the answer.":
                print(f"Found response with assistant {assistant}")
                response = assistant_response
                break
    
    if response != "I'm sorry, I don't know the answer.":
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})