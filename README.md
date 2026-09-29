# 📚 AI Library Assistant

An intelligent, multimodal AI-powered library assistant built with **Python and Streamlit**. The application helps students, researchers, teachers, librarians, and general library users with research, academic writing, document analysis, catalog searching, citations, information literacy, image understanding, AI image generation, and downloadable file creation.

The application combines **Groq-powered language models**, **Groq Vision**, and **Cloudflare Workers AI / FLUX.2 Klein 4B** into a single conversational interface.

---

## 🚀 Project Overview

**AI Library Assistant** is designed as a centralized AI workspace for library and academic tasks.

Users can interact with the assistant through a chat interface and can:

* Ask general library questions
* Perform research-related tasks
* Summarize documents
* Analyze uploaded files
* Understand images, screenshots, charts, and diagrams
* Search library catalog data
* Get citation and reference assistance
* Get cataloguing and metadata assistance
* Receive information-literacy guidance
* Improve academic/professional writing
* Generate AI images
* Generate downloadable documents
* Maintain multiple chat sessions
* Upload multiple files in a single request
* Communicate in English, Urdu, Roman Urdu, or mixed language

The project uses different AI services depending on the task instead of sending every request through a single model.

---

# ✨ Main Features

## 1. 🤖 AI Library Chat

The main interface provides a conversational AI assistant specifically configured for library, research, and academic use.

The assistant supports:

* Library questions
* Research assistance
* Literature-search strategies
* Academic writing
* Summarization
* Citations and references
* Cataloguing
* Information literacy
* Document analysis
* Image understanding
* Learning assistance

The system maintains conversational context and sends recent conversation history to the AI model.

The project keeps the most recent **12 messages** as conversation context to control prompt size.

---

## 2. 🧠 Automatic Intent Detection

The application automatically determines what the user wants before processing the request.

Supported intents include:

```text
IMAGE_GENERATION
FILE_GENERATION
CATALOG_SEARCH
RESEARCH_ASSISTANT
SUMMARIZER
CITATION_ASSISTANT
CATALOGUING_ASSISTANT
INFORMATION_LITERACY
WRITING_ASSISTANT
LIBRARY_CONTENT
GENERAL_LIBRARY
```

For example:

```text
"Generate a poster for a university library"
→ IMAGE_GENERATION

"Summarize this PDF"
→ SUMMARIZER

"Find books about artificial intelligence"
→ CATALOG_SEARCH

"Create APA references"
→ CITATION_ASSISTANT

"Help me plan my literature review"
→ RESEARCH_ASSISTANT

"Create a PowerPoint presentation"
→ FILE_GENERATION
```

The routing logic ensures that different requests are handled by the appropriate processing pipeline.

---

# 🧩 System Architecture

The application can be viewed as the following pipeline:

```text
                         ┌─────────────────────┐
                         │       User          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Streamlit UI      │
                         │  Chat + Uploads     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Request Processing │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Intent Detection  │
                         └──────────┬──────────┘
                                    │
          ┌───────────────┬─────────┼─────────┬───────────────┐
          │               │         │         │               │
          ▼               ▼         ▼         ▼               ▼
      Groq LLM       Groq Vision  Catalog  File Engine   Cloudflare AI
          │               │         │         │               │
          │               │         │         │               │
          ▼               ▼         ▼         ▼               ▼
     AI Answers       Image       CSV     PDF/DOCX/etc.   AI Images
                     Analysis    Search     Generation
          │               │         │         │               │
          └───────────────┴─────────┴─────────┴───────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Streamlit Output  │
                         │ Chat / Files / Image│
                         └─────────────────────┘
```

---

# 🛠️ Technology Stack

## Programming Language

### Python

The complete application is implemented in Python.

Python is used for:

* Application logic
* AI integrations
* File processing
* Image processing
* Catalog searching
* Document generation
* Session management
* API communication

---

# 🎨 Frontend / UI

## Streamlit

**Streamlit** is used as the primary web application framework.

It provides:

* Chat interface
* File upload interface
* Sidebar
* Chat history
* Download buttons
* Data tables
* Image previews
* Status indicators
* Loading/spinner states
* Session state management

The application uses custom CSS through Streamlit's HTML/CSS rendering capabilities to customize the interface.

The Streamlit page is configured with a wide layout and expanded sidebar.

---

# 🧠 AI / LLM Stack

## Groq

Groq is the primary AI inference provider.

The project uses Groq in two different ways.

### Main LLM

The main language model is accessed through:

```python
ChatGroq
```

using:

```python
langchain_groq
```

The default configured model is:

```text
openai/gpt-oss-120b
```

The model can be changed through the environment variable:

```text
GROQ_MODEL
```

The main LLM handles:

* General library questions
* Research assistance
* Summarization
* Citation assistance
* Cataloguing assistance
* Information literacy
* Writing assistance
* Library content
* Image prompt generation
* Downloadable file content generation
* Presentation structure generation
* Intent routing

The project configures the main model with a low temperature of approximately:

```text
0.2
```

for more controlled responses.

---

# 👁️ Groq Vision

The project also has a separate Groq Vision integration.

It uses the official:

```python
Groq
```

client instead of the LangChain wrapper.

The default vision model configured by the application is:

```text
qwen/qwen3.8-27b
```

This model is responsible for understanding uploaded images.

It can perform tasks such as:

* OCR
* Reading visible text
* Screenshot explanation
* Chart explanation
* Diagram explanation
* Image description
* Object identification
* Visual information extraction
* Image-based questions

The project uses a separate API key:

```text
GROQ_VISION_API_KEY
```

and model configuration:

```text
GROQ_VISION_MODEL
```

---

# 🎨 AI Image Generation

## Cloudflare Workers AI

AI image generation is integrated through the **Cloudflare Workers AI API**.

The application uses:

```text
@cf/black-forest-labs/flux-2-klein-4b
```

as its image-generation model.

Default resolution:

```text
1024 × 1024
```

The image-generation pipeline works in two stages:

```text
User Request
     │
     ▼
Groq LLM
     │
     ▼
Detailed Image Prompt
     │
     ▼
Cloudflare Workers AI
     │
     ▼
FLUX.2 Klein 4B
     │
     ▼
Generated Image
```

The Groq model first converts the user's request into a more detailed image-generation prompt.

The generated image is then returned by Cloudflare, decoded from Base64, converted into an image object using Pillow, displayed inside Streamlit, and made available for download.

---

# 📄 Supported File Uploads

The application supports multiple file uploads.

### Images

```text
.jpg
.jpeg
.png
.webp
.gif
```

### Documents

```text
.pdf
.docx
.pptx
```

### Spreadsheets / Data

```text
.xlsx
.xlsm
.csv
```

### Text

```text
.txt
.md
```

The Streamlit chat input allows multiple files and is configured with a maximum upload size of:

```text
20 MB
```

---

# 📑 Document Processing

Different file formats are processed using specialized Python libraries.

## PDF

Library:

```python
pypdf
```

The application extracts text from each PDF page and combines the extracted content.

---

## Microsoft Word

Library:

```python
python-docx
```

The application extracts text from Word document paragraphs.

---

## PowerPoint

Library:

```python
python-pptx
```

The application:

* Iterates through slides
* Identifies slide numbers
* Extracts text from slide shapes
* Combines the extracted content

---

## Excel

Library:

```python
openpyxl
```

The application:

* Opens XLSX/XLSM files
* Reads workbook sheets
* Extracts sheet names
* Reads spreadsheet rows
* Converts values into text
* Limits extracted rows to the first 1,000 rows per sheet

---

## CSV

Library:

```python
pandas
```

CSV files are loaded into Pandas DataFrames and converted into text for AI processing.

---

## TXT / Markdown

Normal text files are decoded using multiple possible encodings:

```text
UTF-8
UTF-16
Latin-1
```

This improves compatibility with text files created using different encodings.

---

# 🖼️ Image Processing

## Pillow

The project uses:

```python
Pillow
```

for image processing.

Before an uploaded image is sent to the vision model, the application:

1. Opens the image
2. Corrects EXIF orientation
3. Converts the image to RGB
4. Resizes excessively large images
5. Converts it to JPEG
6. Compresses it when necessary
7. Encodes it as Base64
8. Creates a `data:image/jpeg;base64,...` URL
9. Sends it to the vision model

This helps normalize different image formats and reduce compatibility problems.

The source specifically handles issues such as PNG transparency, GIF images, CMYK images, EXIF rotation, very large images, and unusual encodings.

---

# 📚 Library Catalog Search

The application includes a local CSV-based library catalog system.

It automatically looks for one of these files:

```text
library_catalog.csv
catalog.csv
books.csv
```

The catalog is loaded using:

```python
pandas
```

Search is performed across the available columns.

The search is:

* Case-insensitive
* Performed across all columns
* Based on text matching
* Limited to the first 20 matching records

The catalog data is treated as the authoritative source for catalog-specific information.

This means the AI is instructed not to invent:

* Books
* Authors
* ISBNs
* Publishers
* Catalog records
* Availability information

---

# 📥 File Generation

The project can generate downloadable files directly from user requests.

Supported output formats include:

```text
DOCX
PDF
PPTX
XLSX
CSV
TXT
Markdown
```

The general generation pipeline is:

```text
User Request
     │
     ▼
Intent Detection
     │
     ▼
File Generation
     │
     ▼
Groq generates content
     │
     ▼
Format-specific Python generator
     │
     ▼
Downloadable File
```

---

# 📝 DOCX Generation

Library:

```python
python-docx
```

The application can create Word documents with:

* Titles
* Headings
* Paragraphs
* Bullet lists
* Numbered lists

It also applies basic font sizing.

---

# 📕 PDF Generation

Library:

```python
ReportLab
```

The PDF generator uses:

```text
A4 page size
```

and creates:

* Headings
* Paragraphs
* Bullet points
* Spacing
* Basic document styling

---

# 📊 XLSX Generation

Library:

```python
openpyxl
```

The generated Excel file:

* Creates a workbook
* Creates a `Library Data` worksheet
* Detects Markdown tables when possible
* Converts table headers into columns
* Adds rows
* Automatically adjusts column widths
* Limits table rows to 500

If no Markdown table exists, the generated content is placed into a single `Content` column.

---

# 📋 CSV Generation

Library:

```python
pandas
```

If the AI generates a Markdown table, it is converted into a DataFrame and exported as CSV.

Otherwise, each non-empty content line is stored as a row in a `Content` column.

---

# 📄 TXT / Markdown Generation

Plain text and Markdown files are generated directly from the AI-generated content.

Markdown is preserved as Markdown.

TXT output has Markdown formatting cleaned where appropriate.

---

# 📽️ PowerPoint Generation

Libraries:

```python
python-pptx
```

and Groq.

The process is:

```text
User Request
     │
     ▼
Groq creates presentation structure
     │
     ▼
JSON slide structure
     │
     ▼
python-pptx
     │
     ▼
PPTX file
```

The AI creates:

```json
{
  "title": "Presentation title",
  "slides": [
    {
      "title": "Slide title",
      "bullets": [
        "Bullet 1",
        "Bullet 2",
        "Bullet 3"
      ]
    }
  ]
}
```

The Python presentation generator then converts this structure into an actual PowerPoint file.

---

# 💬 Multi-Chat System

The application supports multiple conversations using:

```python
st.session_state
```

Each chat contains information such as:

```text
title
messages
created timestamp
attachment context
attachment names
```

Users can:

* Create a new chat
* Switch between chats
* Clear the current chat
* Delete the current chat
* Continue previous conversation context

The first user request can also become the chat title.

---

# 📎 Attachment Context

Uploaded files are processed before the AI receives the user's request.

The extracted content is stored as attachment context and passed to the AI.

The combined attachment context is limited to approximately:

```text
120,000 characters
```

to prevent excessively large prompts.

Images are additionally stored so that the actual uploaded image can be displayed inside the chat interface.

---

# 🌍 Multilingual Support

The AI is instructed to automatically follow the language and writing style of the user's current request.

Supported interaction styles include:

### English

```text
Explain this research paper.
```

### Urdu Script

```text
اس تحقیق کا خلاصہ بتائیں۔
```

### Roman Urdu

```text
Is research paper ka summary batao.
```

### Mixed Language

```text
Is PDF ka short summary English mein do.
```

The language of the uploaded document does not automatically determine the language of the response.

---

# 🧠 Prompt Engineering

The project contains specialized system prompts for different capabilities.

Examples include:

### Research Assistant

Focuses on:

* Research methodology
* Search strategies
* Literature review
* Source evaluation
* Research planning

### Summarizer

Focuses on:

* Accurate summarization
* Important concepts
* Findings
* Arguments
* Conclusions

### Citation Assistant

Focuses on:

* APA
* MLA
* Chicago
* References
* Bibliographies

without inventing missing bibliographic information.

### Cataloguing Assistant

Focuses on:

* Metadata
* MARC
* DDC
* LCC
* Subject headings
* Bibliographic description

### Information Literacy

Focuses on:

* Source credibility
* Authority
* Relevance
* Bias
* Evidence
* Search strategies

### Writing Assistant

Focuses on:

* Grammar
* Clarity
* Rewriting
* Academic writing
* Professional communication

---

# 🔐 Environment Variables

The application uses `python-dotenv` and loads configuration from a `.env` file.

Required environment variables:

```env
GROQ_API_KEY=your_groq_api_key

GROQ_VISION_API_KEY=your_groq_vision_api_key

CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id

CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
```

Optional model configuration:

```env
GROQ_MODEL=openai/gpt-oss-120b

GROQ_VISION_MODEL=qwen/qwen3.8-27b
```

The image model is configured in the application as:

```text
@cf/black-forest-labs/flux-2-klein-4b
```

---

# 📦 Core Python Dependencies

The project imports the following major packages:

```text
streamlit
pandas
requests
Pillow
python-dotenv
groq
langchain-groq
langchain-core
pypdf
python-docx
python-pptx
openpyxl
reportlab
```

Standard-library modules are also used extensively:

```text
os
re
json
base64
html
datetime
io
```

The source code imports these libraries directly for the application's UI, AI integrations, file processing, document generation, and image handling.

> **Note:** The supplied source does not contain pinned package versions. A `requirements.txt` should therefore be created separately if the repository does not already contain one.

---

# 🔌 External Integrations

## 1. Groq API

Used for:

* Main language model
* Intent routing
* Research assistance
* Summarization
* Writing
* Citations
* Cataloguing
* File content generation
* Image prompt generation

The main Groq client is cached with Streamlit's resource caching mechanism.

---

## 2. Groq Vision API

Used for:

* OCR
* Image analysis
* Screenshot analysis
* Diagram understanding
* Chart interpretation
* Visual question answering

Uploaded images are normalized and encoded before being sent to the vision model.

---

## 3. Cloudflare Workers AI

Used for AI image generation.

The application sends the generated image prompt to the Cloudflare AI endpoint and processes the returned Base64 image data.

---

## 4. Local CSV Catalog

The catalog system does not currently connect to an external library management system.

Instead, it checks for:

```text
library_catalog.csv
catalog.csv
books.csv
```

and searches the selected CSV locally using Pandas.

---

# 🗂️ Suggested Repository Structure

A clean GitHub repository can use the following structure:

```text
ai-library-assistant/
│
├── app.py
│
├── library_catalog.csv
│
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
└── assets/
    └── screenshots/
```

If the project is later modularized, a larger architecture could become:

```text
ai-library-assistant/
│
├── app.py
│
├── config.py
│
├── services/
│   ├── groq_service.py
│   ├── vision_service.py
│   ├── cloudflare_service.py
│   ├── catalog_service.py
│   └── file_service.py
│
├── generators/
│   ├── pdf_generator.py
│   ├── docx_generator.py
│   ├── pptx_generator.py
│   ├── xlsx_generator.py
│   └── csv_generator.py
│
├── utils/
│   ├── image_utils.py
│   ├── prompts.py
│   └── routing.py
│
├── data/
│   └── library_catalog.csv
│
├── assets/
│   └── screenshots/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

The current implementation is primarily contained in a single Python application rather than being separated into these modules.

---

# ▶️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-library-assistant.git
cd ai-library-assistant
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

If a requirements file has not yet been created, install the packages used by the project:

```bash
pip install streamlit pandas requests pillow python-dotenv groq langchain-groq langchain-core pypdf python-docx python-pptx openpyxl reportlab
```

---

# 🔑 Configuration

Create a file named:

```text
.env
```

Example:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_VISION_API_KEY=your_groq_vision_api_key

GROQ_MODEL=openai/gpt-oss-120b
GROQ_VISION_MODEL=qwen/qwen3.8-27b

CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
```

Never commit the real `.env` file to GitHub.

Create:

```text
.env.example
```

instead.

Example:

```env
GROQ_API_KEY=
GROQ_VISION_API_KEY=

GROQ_MODEL=openai/gpt-oss-120b
GROQ_VISION_MODEL=qwen/qwen3.8-27b

CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=
```

---

# ▶️ Running the Application

Start the Streamlit application with:

```bash
streamlit run app.py
```

Streamlit will provide a local URL, typically:

```text
http://localhost:8501
```

---

# 📚 Adding a Library Catalog

To enable catalog search, add one of the following files to the application directory:

```text
library_catalog.csv
```

or:

```text
catalog.csv
```

or:

```text
books.csv
```

The application automatically searches for these filenames.

A catalog can contain columns such as:

```text
Title
Author
ISBN
Publisher
Year
Category
Subject
Availability
```

The exact schema is flexible because the search implementation searches across all available columns.

---

# 🔄 Request Processing Flow

A typical request follows this pipeline:

```text
1. User enters request
        ↓
2. Streamlit receives text/files
        ↓
3. Uploaded files are processed
        ↓
4. Images are sent through Vision
        ↓
5. Documents are converted to text
        ↓
6. Attachment context is created
        ↓
7. Intent is detected
        ↓
8. Appropriate processing pipeline is selected
        ↓
9. AI/API/local catalog processing occurs
        ↓
10. Result is displayed in Streamlit
        ↓
11. Generated files/images become downloadable
```

---

# 🖼️ Image Upload Flow

```text
User uploads image
       ↓
Pillow opens image
       ↓
EXIF orientation correction
       ↓
RGB conversion
       ↓
Resize if necessary
       ↓
JPEG compression
       ↓
Base64 encoding
       ↓
Groq Vision
       ↓
Visual analysis
       ↓
Response displayed in chat
```

## The implementation also avoids sending an uploaded image to the Vision model twice during the same request.

# 📄 Document Analysis Flow

```text
Upload document
       ↓
Detect file extension
       ↓
Select extraction engine
       ↓
Extract text/data
       ↓
Combine attachment context
       ↓
Limit context size
       ↓
Send context to Groq
       ↓
AI analyzes / summarizes / answers
       ↓
Display result
```

Supported extraction engines include `pypdf`, `python-docx`, `python-pptx`, `openpyxl`, and Pandas.

---

# 🖼️ AI Image Generation Flow

```text
User:
"Create an image of a modern university library"
             ↓
Intent Detection
             ↓
IMAGE_GENERATION
             ↓
Groq Prompt Engineer
             ↓
Detailed visual prompt
             ↓
Cloudflare Workers AI
             ↓
FLUX.2 Klein 4B
             ↓
1024 × 1024 image
             ↓
Pillow
             ↓
Streamlit preview
             ↓
PNG download
```

The image-generation model and 1024×1024 defaults are configured in the source.

---

# 📥 Downloadable File Flow

```text
User asks for file
       ↓
File-generation intent detected
       ↓
Groq creates content
       ↓
Requested format detected
       ↓
Format-specific generator
       ↓
Binary file created in memory
       ↓
Streamlit download button
```

Supported generated formats:

| Format | Generator   |
| ------ | ----------- |
| DOCX   | python-docx |
| PDF    | ReportLab   |
| PPTX   | python-pptx |
| XLSX   | openpyxl    |
| CSV    | Pandas      |
| TXT    | Python      |
| MD     | Python      |

---

# 🧠 State Management

The application currently uses:

```python
st.session_state
```

instead of an external database.

Session state stores:

* Chat sessions
* Current chat
* Chat counter
* Generated image
* Generated file
* Attachment context
* Attachment names
* Messages

This makes the application lightweight and easy to run without setting up a database.

---

# ⚡ Caching

Streamlit caching is used for expensive/reusable resources.

Examples include:

```python
@st.cache_resource
```

for AI clients and:

```python
@st.cache_data
```

for catalog data.

This reduces unnecessary recreation of AI clients and repeated catalog loading.

---

# 🎨 UI Features

The interface includes:

* Wide Streamlit layout
* Expanded sidebar
* Custom CSS
* Chat interface
* Chat history
* New Chat button
* Clear Chat button
* Delete Chat button
* Attachment chips
* Image previews
* Generated image preview
* Generated file download
* Copy-to-clipboard button
* Loading indicators
* API connection status
* Responsive data tables

The sidebar also displays the current system/API status.

---

# 🔒 Security Considerations

API credentials are loaded through environment variables rather than being hard-coded into the application.

Recommended `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
.streamlit/secrets.toml
```

Never commit:

```text
GROQ_API_KEY
GROQ_VISION_API_KEY
CLOUDFLARE_API_TOKEN
```

or other private credentials.

---

# ⚠️ Current Limitations

The current implementation is intentionally lightweight.

### No external database

Chat history is stored in Streamlit session state, so it is not a persistent multi-user database.

### No authentication

There is currently no login, user account, role management, or authentication system implemented.

### Local catalog only

Catalog search currently uses local CSV files rather than a live library management system or external library API.

### No vector database / RAG

The current system does not implement:

```text
FAISS
Chroma
Pinecone
Weaviate
Qdrant
Elasticsearch
```

or another vector database.

Uploaded documents are extracted into text and passed as context to the language model.

### Prompt-size limitation

Combined uploaded-file context is intentionally limited to approximately 120,000 characters.

### Catalog search limitation

Catalog search is basic text matching rather than semantic/vector search.

### File extraction limitation

The current document pipeline primarily extracts textual content. Complex document layouts, embedded media, scanned PDFs, and advanced spreadsheet structures may require additional processing.

---

# 🧪 Example Use Cases

## Students

```text
"Summarize this research paper."

"Explain this chapter in simple language."

"Create APA references for these sources."

"Make a presentation about artificial intelligence."

"Generate a study guide from this PDF."
```

## Researchers

```text
"Help me plan a literature review."

"Suggest keywords for this research topic."

"Evaluate the credibility of this source."

"Summarize these research documents."
```

## Librarians

```text
"Help classify this book using DDC concepts."

"Create a library awareness poster."

"Search the library catalog for books about databases."

"Create an announcement for library week."
```

## Teachers / Faculty

```text
"Create a lecture presentation."

"Generate a PDF handout."

"Summarize this academic document."

"Create a spreadsheet from this information."
```

---

# 🏗️ Design Philosophy

The application follows a modular processing concept even though the current implementation is primarily contained in one Python application.

Different technologies are used for different jobs:

```text
Streamlit
    → User interface

Groq LLM
    → Reasoning and text generation

Groq Vision
    → Image understanding

Cloudflare Workers AI
    → Image generation

Pandas
    → Catalog/data processing

Pillow
    → Image processing

pypdf
    → PDF extraction

python-docx
    → Word processing

python-pptx
    → PowerPoint processing

openpyxl
    → Excel processing

ReportLab
    → PDF creation
```

This separation allows the project to combine text AI, vision AI, local structured data, document processing, and generative media in one application.

---

# 📊 Technology Summary

| Category              | Technology              |
| --------------------- | ----------------------- |
| Language              | Python                  |
| Web Framework         | Streamlit               |
| Main LLM Provider     | Groq                    |
| Main LLM Integration  | LangChain Groq          |
| Default LLM           | `openai/gpt-oss-120b`   |
| Vision Provider       | Groq                    |
| Default Vision Model  | `qwen/qwen3.8-27b`      |
| Image Generation      | Cloudflare Workers AI   |
| Image Model           | FLUX.2 Klein 4B         |
| Image Processing      | Pillow                  |
| Data Processing       | Pandas                  |
| PDF Reading           | pypdf                   |
| Word Processing       | python-docx             |
| PowerPoint Processing | python-pptx             |
| Excel Processing      | openpyxl                |
| PDF Generation        | ReportLab               |
| Configuration         | python-dotenv           |
| HTTP/API Requests     | requests                |
| State Management      | Streamlit Session State |
| Catalog Storage       | Local CSV               |
| Database              | None                    |
| Vector Database       | None                    |
| Authentication        | None                    |

---

# 🔮 Future Improvements

Possible future upgrades include:

* User authentication
* Persistent database
* PostgreSQL integration
* Real library-management-system integration
* OPAC/API integration
* Semantic catalog search
* Vector database / RAG
* Embeddings
* OCR for scanned PDFs
* Better table extraction
* Persistent chat history
* User accounts
* Admin dashboard
* Library staff dashboard
* Usage analytics
* Document preview
* Citation verification
* More AI model providers
* Streaming responses
* Background processing for large files
* Cloud storage integration
* Production deployment
* Role-based access control

---

# 📜 Project Purpose

The purpose of **AI Library Assistant** is to provide a single AI-powered environment for library users to interact with information, documents, research material, catalog data, and generative AI tools.

Instead of requiring separate tools for:

```text
Chat
Research
Document Analysis
Image Analysis
Catalog Search
Image Generation
Document Generation
```

the application combines these capabilities into one Streamlit-based interface.

---

# 👨‍💻 Creator

**Created by Hafiz Subhan Amir**

---

# 📄 License

Add your preferred license here.

For example:

```text
MIT License
```

If this project is intended for commercial or proprietary use, replace this section with the appropriate license and ownership terms.

---

# ⭐ Summary

**AI Library Assistant** is a multimodal AI library platform built with Python and Streamlit.

It combines:

```text
Python
+
Streamlit
+
Groq LLM
+
Groq Vision
+
LangChain
+
Cloudflare Workers AI
+
FLUX.2 Klein 4B
+
Pillow
+
Pandas
+
pypdf
+
python-docx
+
python-pptx
+
openpyxl
+
ReportLab
```

to provide:

**AI chat + research assistance + document analysis + image understanding + catalog search + academic assistance + AI image generation + downloadable document generation**

in one application.
