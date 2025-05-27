from core.vector_store import vector_store

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA

retriever_model = ChatOllama(model="qwen3:0.6b", temperature=0)

retriever = vector_store.as_retriever()

retriever_prompt = PromptTemplate(
    input_variables=["question"],
    template="""
    You are a multilingual query rewriter helping improve document retrieval from a vector database.
    Your task is to generate several diverse reformulations of the input query to maximize recall.
    Include at least 2 queries in Russian and 2 in English. Rephrase the query using:
    
    - Synonyms
    - Common phrases
    - Abbreviations and their expansions
    - Related technical or domain-specific terms
    - Alternative grammatical structures
    
    Original user question: {question}
    
    Return 6–8 diverse, semantically related queries in a list format. Avoid exact duplicates. 
    Ensure both Russian and English are represented.
    """,
)

retriever_from_llm = MultiQueryRetriever.from_llm(
    retriever=retriever, llm=retriever_model,
    prompt=retriever_prompt
)

base_prompt = """You're a personal AI assistant.
Don't tell the user about the context!
Don't talk to the user about unnecessary topics other than the topic of context!
Rely ONLY on the suggested context, only occasionally adding something of your own.
If the user asks about something else out of context, 
tell him "Данный вопрос находится вне данной мне базы знаний"
Along with the response, send the sources from the metadata.

Answer only on Russian, but you can think in whatever language you want.
Present all mathematical formulas in LaTeX format.

Answer the question based only on the following context:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(base_prompt)

ollama_llm = "qwen3:8b"
model_local = ChatOllama(model=ollama_llm, temperature=0)

chain = (
    {"context": retriever_from_llm, "question": RunnablePassthrough()}
    | prompt
    | model_local
    | StrOutputParser()
)

if __name__ == "__main__":
    while True:
        user_prompt = input(">> ")
        if user_prompt == "/bye":
            break

        print("AI: ", end="")
        answer = ""
        for chunk in chain.stream(user_prompt):
            answer += chunk
            print(chunk, end="")
        print()
