# LabourLens: An AI-powered chatbot for tracking labor market trends 📊

## Motivation
- Labor market data is scattered across reports and sources
- It’s a struggle to access or interpret these trends.

## Overview  
The **LabourLens** leverages **Retrieval-Augmented Generation (RAG)** to analyze and respond to questions about how **AI transformation** is impacting the labor market. By utilizing a **knowledge source** of indexed documents, the chatbot provides up-to-date and data-driven insights on job trends, emerging skills, and industry shifts.  

Try it out: https://job-trends-agent.onrender.com/
## Key Features  
- ✅ **AI-Driven Insights** – Uses **RAG** to retrieve relevant information and generate contextual responses.  
- ✅ **Live Document Indexing** – Continuously updates its knowledge base with **job market reports, research papers, and industry insights**.  
- ✅ **Multi-Format Support** – Processes text, CSV, PDF, and images to extract labor market insights.  
- ✅ **Efficient Query Handling** – Avoids redundant processing with **intelligent caching and indexing**.  
- ✅ **Conversational AI** – Engages users with natural language responses based on real-time data retrieval.  

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


