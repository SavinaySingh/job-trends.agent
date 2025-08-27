import os
import pickle
import time
from PIL import Image
from sentence_transformers import SentenceTransformer
from annoy import AnnoyIndex
import json
from tqdm import tqdm
import shutil
from rag_app.utils.chunking import split_text_file, split_csv_data
from rag_app.utils.pdf_to_image import pdf_to_images
from google.generativeai.generative_models import GenerativeModel


def process_and_update_index(
    new_file_path,
    llm: GenerativeModel,
    knowledge_dir="data/knowledge_source",
    pickle_dir="data/PickleFiles",
    annoy_index_path="vector_store/annoy_st_index.ann",
    doc_mapping_path="data/doc_mapping.json",
    model_name="all-MiniLM-L6-v2",
    n_trees=10,
):
    """
    Add a new file to knowledge source, process it, save pickle, then update Annoy index and doc mapping.
    """
    print(f"Processing new file: {new_file_path}")

    basename = os.path.basename(new_file_path)
    dest_path = os.path.join(knowledge_dir, basename)
    if os.path.abspath(new_file_path) != os.path.abspath(dest_path):
        shutil.copyfile(new_file_path, dest_path)
    else:
        print(f"File already in destination: {dest_path}")
    print(f"Copied file {basename} to knowledge source folder.")

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
