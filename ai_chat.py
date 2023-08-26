import os
import openai
import langchain
import panel as pn
import param


from langchain.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain


embeddings = OpenAIEmbeddings()
llm_name = "gpt-3.5-turbo"
llm = ChatOpenAI(model_name = llm_name, temperature = 0)


# Load documents into vector stores
# ----------------------------------------------------------------
# all_texts = []
# folder_name = "patents"
# for file_name in os.listdir(os.path.join('docs', folder_name)):
#     try:
#         all_texts += Docx2txtLoader(os.path.join('.', 'docs', folder_name, file_name)).load()
#     except:
#         print(f"cannot read {os.path.join('.', 'docs', folder_name, file_name)}")
# folder_name = "lectures"
# for file_name in os.listdir(os.path.join('docs', folder_name)):
#     try:
#         all_texts += Docx2txtLoader(os.path.join('.', 'docs', folder_name, file_name)).load()
#     except:
#         print(f"cannot read {os.path.join('.', 'docs', folder_name, file_name)}")
# folder_name = "articles"
# for file_name in os.listdir(os.path.join('docs', folder_name)):
#     try:
#         all_texts += Docx2txtLoader(os.path.join('.', 'docs', folder_name, file_name)).load()
#     except:
#         print(f"cannot read {os.path.join('.', 'docs', folder_name, file_name)}")

# text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 0)
# vectorstore = Chroma.from_documents(documents = text_splitter.split_documents(all_texts), 
#                                     embedding = embeddings, 
#                                     persist_directory = os.path.join(".", "docs", "merged_vectorstore"))
# ----------------------------------------------------------------


vectorstore = Chroma(persist_directory=os.path.join(".", "docs", "merged_vectorstore"), embedding_function = embeddings)


# Basic example
# ----------------------------------------------------------------
# question = "How many poles shoul my electromotor have, and what should I do if I have the wrong number?"
# qa_chain = RetrievalQA.from_chain_type(llm = llm, retriever = vectorstore.as_retriever())
# print(qa_chain({"query": question}))
# ----------------------------------------------------------------


# ConversationalRetrievalChain example
# ----------------------------------------------------------------
memory = ConversationBufferMemory(memory_key = "chat_history", return_messages = True)
retriever = vectorstore.as_retriever()
qa = ConversationalRetrievalChain.from_llm(llm = llm, retriever = retriever, memory = memory)
question = input()
print(f"Question: {question}")
print(f"Answer: {qa({'question': question})['answer']}")
question = input()
print(f"Question: {question}")
print(f"Answer: {qa({'question': question})['answer']}")
# ----------------------------------------------------------------



# ----------------------------------------------------------------
# def load_db(chain_type, k):
#     # define retriever
#     retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": k})
#     # create a chatbot chain. Memory is managed externally.
#     qa = ConversationalRetrievalChain.from_llm(
#         llm = llm, 
#         chain_type = chain_type, 
#         retriever = retriever, 
#         return_source_documents = True,
#         return_generated_question = True,
#     )
#     return qa 

# class cbfs(param.Parameterized):
#     chat_history = param.List([])
#     answer = param.String("")
#     db_query  = param.String("")
#     db_response = param.List([])
    
#     def __init__(self,  **params):
#         super(cbfs, self).__init__( **params)
#         self.panels = []
#         self.qa = load_db("stuff", 4)

#     def convchain(self, query):
#         if not query:
#             return pn.WidgetBox(pn.Row('User:', pn.pane.Markdown("", width=600)), scroll=True)
#         result = self.qa({"question": query, "chat_history": self.chat_history})
#         self.chat_history.extend([(query, result["answer"])])
#         self.db_query = result["generated_question"]
#         self.db_response = result["source_documents"]
#         self.answer = result['answer'] 
#         self.panels.extend([
#             pn.Row('User:', pn.pane.Markdown(query, width=600)),
#             pn.Row('ChatBot:', pn.pane.Markdown(self.answer, width=600, style={'background-color': '#F6F6F6'}))
#         ])
#         inp.value = ''  #clears loading indicator when cleared
#         return pn.WidgetBox(*self.panels,scroll=True)

#     @param.depends('db_query ', )
#     def get_lquest(self):
#         if not self.db_query :
#             return pn.Column(
#                 pn.Row(pn.pane.Markdown(f"Last question to DB:", styles={'background-color': '#F6F6F6'})),
#                 pn.Row(pn.pane.Str("no DB accesses so far"))
#             )
#         return pn.Column(
#             pn.Row(pn.pane.Markdown(f"DB query:", styles={'background-color': '#F6F6F6'})),
#             pn.pane.Str(self.db_query )
#         )

#     @param.depends('db_response', )
#     def get_sources(self):
#         if not self.db_response:
#             return 
#         rlist=[pn.Row(pn.pane.Markdown(f"Result of DB lookup:", styles={'background-color': '#F6F6F6'}))]
#         for doc in self.db_response:
#             rlist.append(pn.Row(pn.pane.Str(doc)))
#         return pn.WidgetBox(*rlist, width=600, scroll=True)

#     @param.depends('convchain', 'clr_history') 
#     def get_chats(self):
#         if not self.chat_history:
#             return pn.WidgetBox(pn.Row(pn.pane.Str("No History Yet")), width=600, scroll=True)
#         rlist=[pn.Row(pn.pane.Markdown(f"Current Chat History variable", styles={'background-color': '#F6F6F6'}))]
#         for exchange in self.chat_history:
#             rlist.append(pn.Row(pn.pane.Str(exchange)))
#         return pn.WidgetBox(*rlist, width=600, scroll=True)

#     def clr_history(self,count=0):
#         self.chat_history = []
#         return 
    

# cb = cbfs()

# # file_input = pn.widgets.FileInput(accept='.pdf')
# # button_load = pn.widgets.Button(name="Load DB", button_type='primary')
# # button_clearhistory = pn.widgets.Button(name="Clear History", button_type='warning')
# # button_clearhistory.on_click(cb.clr_history)
# inp = pn.widgets.TextInput( placeholder='Enter text here…')

# # bound_button_load = pn.bind(cb.call_load_db, button_load.param.clicks)
# conversation = pn.bind(cb.convchain, inp) 

# jpg_pane = pn.pane.Image( './img/convchain.jpg')

# tab1 = pn.Column(
#     pn.Row(inp),
#     pn.layout.Divider(),
#     pn.panel(conversation,  loading_indicator=True, height=300),
#     pn.layout.Divider(),
# )
# tab2= pn.Column(
#     pn.panel(cb.get_lquest),
#     pn.layout.Divider(),
#     pn.panel(cb.get_sources ),
# )
# tab3= pn.Column(
#     pn.panel(cb.get_chats),
#     pn.layout.Divider(),
# )
# dashboard = pn.Column(
#     pn.Row(pn.pane.Markdown('# ChatWithYourData_Bot')),
#     pn.Tabs(('Conversation', tab1), ('Database', tab2), ('Chat History', tab3))
# )

# dashboard
# ----------------------------------------------------------------





