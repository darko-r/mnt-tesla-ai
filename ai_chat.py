import os
import openai
import langchain

from langchain.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

embeddings = OpenAIEmbeddings()

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
question = "How many poles shoul my electromotor have, and what should I do if I have the wrong number?"
docs = vectorstore.similarity_search(question)
print(len(docs))
print(docs)

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
qa_chain = RetrievalQA.from_chain_type(llm, retriever=vectorstore.as_retriever())
print(qa_chain({"query": question}))









