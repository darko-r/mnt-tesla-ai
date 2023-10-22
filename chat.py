from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

llm_name = "gpt-3.5-turbo"
llm = ChatOpenAI(model_name = llm_name, temperature = 0)

embeddings = OpenAIEmbeddings()

vectorstore = Chroma(persist_directory=f"./vectorstore_nltk", embedding_function = embeddings)

metadata_field_info = [
    AttributeInfo(
        name="category",
        description="Category of te text content - possible values are NarrativeText and Title",
        type="string",
    ),
    AttributeInfo(
        name="year",
        description="Year when the document was published",
        type="integer",
    ),
    AttributeInfo(
        name="applicant",
        description="Name of the person that filed the patent",
        type="string",
    ),
    AttributeInfo(
        name="day",
        description="Day when the document was published",
        type="integer",
    ),
    AttributeInfo(
        name="month",
        description="Month when the document was published",
        type="integer",
    ),
    AttributeInfo(
        name="filename",
        description="Name of the file",
        type="string",
    ),
    AttributeInfo(
        name="id",
        description="Document ID",
        type="string",
    ),
    AttributeInfo(
        name="page_number",
        description="Page number from the original document",
        type="string",
    ),
    AttributeInfo(
        name="register_num",
        description="Patent registration number",
        type="string",
    ),
    AttributeInfo(
        name="source",
        description="Source that published the document.",
        type="string",
    ),
    AttributeInfo(
        name="title",
        description="Document title",
        type="string",
    ),
    AttributeInfo(
        name="type",
        description="Type of the document - possible value are article, lecture and patent",
        type="string",
    ),
]

document_content_description = "Document content"

base_retriever = vectorstore.as_retriever(search_type = 'mmr', search_kwargs = {'k': 2})
multi_query = MultiQueryRetriever.from_llm(retriever = base_retriever, llm = llm)
self_query_retriever = SelfQueryRetriever.from_llm(llm = llm, vectorstore = vectorstore, document_contents = document_content_description,
                                                   metadata_field_info = metadata_field_info, verbose=True)
ensemble_retriever = EnsembleRetriever(retrievers = [multi_query, self_query_retriever])

prompt_template = PromptTemplate.from_template(
    """Let's think step by step. Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to
    make up an answer.

    Context:
    {context}

    Question: {question}
    Helpful Answer:"""
)

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
chain = ConversationalRetrievalChain.from_llm(llm = llm, 
                                              retriever = ensemble_retriever, 
                                              chain_type = 'map_reduce',
                                              memory = memory)

chat_history = []
def convchain():
    while True:
        prompt = input('Enter a prompt...')
        if not prompt:
            print("NO INPUT!")
        result = chain({"question": prompt, "chat_history": chat_history})
        chat_history.extend([(prompt, result["answer"])])
        answer = result['answer']
        print(f"HISTORY: {chat_history}")
        print(f"PROMPT: {prompt}")
        print(f"ANSWER: {answer}")

convchain()