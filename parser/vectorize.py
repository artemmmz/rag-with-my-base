import json
from pathlib import Path

from core.config import GeneralSettings
from core.vector_store import vector_store

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

DATASET_FILES = [
    {
        "dataset_filename": GeneralSettings.ROOT_DIR / "parser/arxiv/arxiv_dataset.jsonl",
        "format": "latex"
    },
    {
        "dataset_filename": GeneralSettings.ROOT_DIR / "parser/wiki-sites/ifmo_dataset.jsonl",
    },
]


def save_documents(dataset_filename: str | Path, format: str = "text"):
    if isinstance(dataset_filename, Path):
        dataset_filename = dataset_filename.as_posix()
    if format == "latex" or format == "markdown":
      splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN, chunk_size=700, chunk_overlap=0
      )
    elif format == "text":
      splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=0)
    else:
        print("Incorrect format")
        return
    with open(dataset_filename, mode="r") as dataset_file_in:
        print(f"Current file: {dataset_filename}")
        for data_raw in dataset_file_in.readlines():
            data: dict[str, str | int | float] = json.loads(data_raw)
            print(f"Current document with title: {data.get('title')}")
            main_document = Document(page_content=data.pop("content"), metadata=data)
            documents = splitter.split_documents([main_document])
            try:
              print(f"Saving {len(documents)} documents")
              ids = vector_store.add_documents(documents)
              print(f"Saved documents ids: {ids}")
            except Exception as e:
              print(f"Error: {e}")
              continue

if __name__ == "__main__":
    for dataset in DATASET_FILES:
        save_documents(**dataset)
