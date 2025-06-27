# LabourLens: Understanding impact of AI on Labour Market 📈

## Motivation
- Labor market data is scattered across reports and sources
- It’s a struggle to access or interpret these trends.

## Overview  
**LabourLens** uses a combination of **Retrieval-Augmented Generation (RAG)** and **HyDE (Hypothetical Document Embeddings)** to analyze and respond to questions about the impact of **AI transformation** on the labor market. By utilizing a **knowledge source** of indexed documents, the chatbot provides up-to-date and data-driven insights on job trends, emerging skills, and industry shifts.  

- Try it out: https://job-trends-agent.onrender.com/
- Video 🎥: https://drive.google.com/file/d/1Blawr5Tm8rDynljHn9mX4JB7zEntrQ4B/view?usp=drive_link
  
## Design Decisions

<p align="center">
  <img src="https://github.com/user-attachments/assets/83d873c4-9db2-49f4-b82b-ec00147ea2d6" width="600"/>
</p>

- 🚀 **Multi-Format Support** – Processes text, CSV, PDF, and images to extract labor market insights.  
- 🧠 **Conversational AI** – Engages users through natural language responses powered by real-time data retrieval and enhanced with context-buffer memory.  
- ⚡ **Efficient Semantic Search** – Uses **HNSW indexing via FAISS** for fast and accurate retrieval of relevant information from the document store.  
- 🎯 **Planned Ensemble Prompting** – Aims to minimize hallucinations by combining multiple prompts, though currently not implemented due to Gemini’s rate limiting.

## How It Works  

### 1. **Document Ingestion**  
- The chatbot scans a **knowledge source** (`./knowledge_source`) for new or updated files.  
- It processes text, CSV, PDF, and image-based documents, extracting **key labor market insights**.  
- Indexed data is stored using **pickle-based caching** for fast retrieval.  

### 2. **Retrieval-Augmented Generation (RAG)**  
- When a user asks a question, the chatbot searches the **indexed documents** for relevant information.  
- It retrieves the most **contextually relevant** chunks of data and feeds them into an LLM.  
- The LLM generates an informative and well-structured response based on retrieved content.  

### 3. **Query Handling & Response Generation**  
The chatbot provides answers about:  
- 📈 **Job market trends** (growth/decline of roles)  
- 🤖 **AI's impact on different industries**  
- 🎓 **Skills and qualifications in demand**  
- 🌍 **Geographical job distribution shifts**  

## Installation & Setup  

### 1. **Clone the Repository**  
```bash
git clone https://github.com/your-repo/job-trend-agent.git
cd job-trend-agent
```
### 2. **Install Dependencies**
```
pip install -r requirements.txt
```

### 3. **Prepare Knowledge Source**
Place reports, research papers, and job market datasets in the ./knowledge_source folder.
The chatbot will index these automatically.

### 4. **Run the Chatbot**
```
python manage.py runserver
```

## Future Enhancements
🔹 Integration with live job market APIs for real-time updates.
🔹 Personalized recommendations for career planning.


## License
📜 MIT License – Free to use and modify.


