from core.config import GeneralSettings

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

vector_store = Chroma(
    collection_name="base_collection",
    embedding_function=embeddings,
    persist_directory=(GeneralSettings.ROOT_DIR / "chroma.db").as_posix(),
)
