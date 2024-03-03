import streamlit as st
import time
from openai import OpenAI
from helper import all_assistants, json_entry_list, classifier_prompt, condition_parse_prompt, classify, parse_condition
import re

"""
TODO
    done - copy all from langchian here
    done - integrade cond_parser 
    done - integrate classifier
    - write final_ret
    - write get_file_name
    - search branch
    - LangChain tidy-up
    - parse and print citation
    - multiple count()
"""



st.title("Simple chat")
client = OpenAI()
user_thread = client.beta.threads.create()

@st.cache_data
def load_assistants():
    return all_assistants()

@st.cache_data
def load_assistants(path):
    return json_entry_list(path)

file_assistants = load_assistants()
json_entry_list_ = json_entry_list('metadata.json')

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def response_generator():
    response = "Hello there! How can I assist you today?"
     
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

if prompt := st.chat_input("What is up?"):
    thread_message = client.beta.threads.messages.create(
        thread_id = user_thread.id,
        role = "user",
        content = prompt,
    )
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    class_ = classify(prompt)
    if class_.lower() == "logic":
        conditions = parse_condition(prompt)
        if "count" in conditions.lower():
            cnt = json_entry_list_.count(conditions[6:-1])
            # TODO: LLM for nice output
        else:
            list = json_entry_list_.fetch(conditions)
            # TODO: Write just list?
    elif class_.lower() == "summarize":
        pass
    else:
        # assistant = metadata_assistant
        assistant = file_assistants[0]
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
        response = re.sub('【.*】', '', last_msg.content[0].text.value)
        if response != "I'm sorry, I don't know the answer.":
            print(f"response found with assistant {assistant}")
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})