import os
import pickle
import time
from PIL import Image
from pdf2image import convert_from_path
from langchain.text_splitter import CharacterTextSplitter
from sentence_transformers import SentenceTransformer
from annoy import AnnoyIndex
import json
from tqdm import tqdm
import shutil


def process_and_update_index(
    new_file_path,
    knowledge_dir="data/knowledge_source",
    pickle_dir="data/PickleFiles",
    annoy_index_path="annoy_st_index.ann",
    doc_mapping_path="doc_mapping.json",
    llm=None,
    model_name="all-MiniLM-L6-v2",
    chunk_size=1000,
    n_trees=10,
):
    """
    Add a new file to knowledge source, process it, save pickle, then update Annoy index and doc mapping.

    Args:
        new_file_path (str): Full path to the new file to add.
        knowledge_dir (str): Directory where knowledge source files are stored.
        pickle_dir (str): Directory where pickle files are stored.
        annoy_index_path (str): Path to saved Annoy index file.
        doc_mapping_path (str): Path to saved doc mapping JSON file.
        llm: Initialized LLM object to summarize images (if needed). If None, skip summarization.
        model_name (str): SentenceTransformer model name.
        chunk_size (int): Chunk size for splitting text.
        n_trees (int): Number of trees for Annoy index build.
    """
    print(f"Processing new file: {new_file_path}")
    # Copy file into knowledge_dir
    basename = os.path.basename(new_file_path)
    dest_path = os.path.join(knowledge_dir, basename)
    if os.path.abspath(new_file_path) != os.path.abspath(dest_path):
        shutil.copyfile(new_file_path, dest_path)
    else:
        print(f"File already in destination: {dest_path}")
    print(f"Copied file {basename} to knowledge source folder.")

    # Helper functions (copy from your code)
    def split_text_file(file_path, chunk_size=chunk_size):
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
        text_splitter = CharacterTextSplitter(
            separator="\n", chunk_size=chunk_size, chunk_overlap=200
        )
        return text_splitter.split_text(text)

    def read_csv_as_text(file_path):
        import csv

        rows_as_text = []
        with open(file_path, mode="r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader)  # Skip header
            for row in csv_reader:
                row_text = " | ".join(row)
                rows_as_text.append(row_text)
        return rows_as_text

    def split_csv_data(file_path, chunk_size=chunk_size):
        rows_as_text = read_csv_as_text(file_path)
        text_splitter = CharacterTextSplitter(
            separator="\n", chunk_size=chunk_size, chunk_overlap=200
        )
        full_text = "\n".join(rows_as_text)
        return text_splitter.split_text(full_text)

    def pdf_to_images(pdf_path):
        return convert_from_path(pdf_path)

    # Process file based on extension
    file_data = {}
    ext = basename.split(".")[-1].lower()
    file_data["type"] = ext
    file_data["pages"] = []

    if ext == "txt":
        print(f"Processing text file: {basename}")
        chunks = split_text_file(dest_path)
        file_data["pages"] = chunks

    elif ext == "csv":
        print(f"Processing CSV file: {basename}")
        chunks = split_csv_data(dest_path)
        file_data["pages"] = chunks

    elif ext == "png":
        print(f"Processing PNG image file: {basename}")
        if llm is None:
            raise ValueError("LLM must be provided to summarize images.")

        image = Image.open(dest_path)

        summary = llm.generate_content(
            ["Summarise the image in more than 1000 words.", image]
        )
        file_data["pages"].append(summary.text)

    elif ext == "pdf":
        print(f"Processing PDF file: {basename}")
        if llm is None:
            raise ValueError("LLM must be provided to summarize PDF images.")

        images = pdf_to_images(dest_path)
        for image in tqdm(images, desc="Summarizing PDF pages"):
            summary = llm.generate_content(
                ["Summarise the image in more than 1000 words.", image]
            )
            file_data["pages"].append(summary.text)
            time.sleep(1)
        time.sleep(10)

    else:
        print(f"Unsupported file type: {basename}, skipping.")
        return

    # Save pickle for this new file
    pickle_file_path = os.path.join(pickle_dir, f"{basename}.pkl")
    with open(pickle_file_path, "wb") as f:
        pickle.dump(file_data, f)
    print(f"Saved processed data to pickle: {pickle_file_path}")

    # Now reload ALL pickle files to rebuild index and doc mapping (to keep it simple and consistent)
    print("Rebuilding index and document mapping with all pickle files...")
    model = SentenceTransformer(model_name)

    all_pages = []
    page_file_mapping = (
        []
    )  # To keep track of which page belongs to which file and page no

    pickle_files = [
        f for f in os.listdir(pickle_dir) if f.endswith(".pkl") or f.endswith(".pickle")
    ]
    for pf in tqdm(pickle_files, desc="Loading pickles for index"):
        with open(os.path.join(pickle_dir, pf), "rb") as f:
            content = pickle.load(f)
            pages = content.get("pages", [])
            all_pages.extend(pages)
            # Keep track of file name and page index for mapping
            for i in range(len(pages)):
                page_file_mapping.append(
                    {
                        "file_name": pf.replace(".pkl", ""),
                        "page_no": i,
                        "text": pages[i],
                    }
                )

    print(f"Total pages for embedding: {len(all_pages)}")

    # Embed all pages
    embeddings = model.encode(
        all_pages,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    dimension = embeddings.shape[1]

    # Build Annoy index
    index = AnnoyIndex(dimension, "angular")
    for i, vector in enumerate(tqdm(embeddings, desc="Adding vectors to Annoy index")):
        index.add_item(i, vector)

    index.build(n_trees)
    index.save(annoy_index_path)
    print(f"Annoy index saved to {annoy_index_path}")

    # Create and save doc mapping
    # Use a dict with string keys (index) and values as page info dict
    doc_mapping = {str(i): page_file_mapping[i] for i in range(len(page_file_mapping))}
    with open(doc_mapping_path, "w") as f:
        json.dump(doc_mapping, f)

    print(f"Document mapping saved to {doc_mapping_path}")
    print("Index and document mapping update complete.")
