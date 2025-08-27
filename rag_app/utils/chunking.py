from langchain.text_splitter import CharacterTextSplitter


def split_text_file(file_path, chunk_size=1000):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=chunk_size, chunk_overlap=200
    )
    return text_splitter.split_text(text)


def split_csv_data(file_path, chunk_size=1000):
    rows_as_text = read_csv_as_text(file_path)
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=chunk_size, chunk_overlap=200
    )
    full_text = "\n".join(rows_as_text)
    return text_splitter.split_text(full_text)


def read_csv_as_text(file_path):
    import csv

    rows_as_text = []
    with open(file_path, mode="r", encoding="utf-8") as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  #
        for row in csv_reader:
            row_text = " | ".join(row)
            rows_as_text.append(row_text)
    return rows_as_text
