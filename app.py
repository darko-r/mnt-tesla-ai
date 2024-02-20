import streamlit as st
import time
from openai import OpenAI
import re

st.title("Simple chat")
client = OpenAI()
assistants = ['asst_X5VLaEo73bi3fuH7DcrZnMF0',
'asst_KH8fvndG7mfHmkcGw4mgzY0P',
'asst_X0iM9rr8BcIaDCjQWGLLqTYk',
'asst_97hGP77njU8eyxhKngUQ70m3',
'asst_YL7bO35whowlEBv02wj3HrU5',
'asst_DWyJySblBPbc4XenM1CFhTwb',
'asst_zs7Ya0NvHUceAjf7Hgcr7Mnb',
'asst_jBPdUspkKT7aYwqLFnh1m8Ht',
'asst_75FXxglIh7vxlscAchB1q2Ok',
'asst_VXHS7jZJrYC1nUAQzHxiNmOl',
'asst_fiEHoZgjfRs3lQi1ozXnqmpE',
'asst_ecJR8agsOGfVmMCefzRnrBuW',
'asst_WGhiAfmQBjs6k8A1tnL5FYQA',
'asst_sbxpi9R2Nji7Rwbz1nW5NJua',
'asst_pDu1qz0HYBiWQGHUsB8DeORl',
'asst_E7d11pusFqaIn6D2xRQA2pff',
'asst_vFUYJOeB1DmE0Ipqat5aiVvz',
'asst_m2BNvI9i076ViYm48SrwLvsh',
'asst_KirbrNKyL9EqaiEwVLFdCGGj']
thread = client.beta.threads.create()


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
        thread_id = thread.id,
        role = "user",
        content = prompt,
    )
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    for assistant in assistants:
        print(f"trying assistant {assistant}")
        run = client.beta.threads.runs.create(
            thread_id = thread.id,
            assistant_id = assistant
        )
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            time.sleep(1)
        
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        last_msg = max(messages.data, key = lambda x: x.created_at)
        response = re.sub('【.*】', '', last_msg.content[0].text.value)
        if response != "I'm sorry, I don't know the answer.":
            print(f"response found with assistant {assistant}")
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            break