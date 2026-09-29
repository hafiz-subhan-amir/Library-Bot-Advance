import os
import re
import json
import base64
import html
import requests
import pandas as pd
import streamlit as st

from datetime import datetime
from io import BytesIO

from PIL import Image, ImageOps
from dotenv import load_dotenv

from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from pypdf import PdfReader
from docx import Document
from pptx import Presentation
from openpyxl import load_workbook, Workbook

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.enums import TA_LEFT

from docx.shared import Pt
from pptx.util import Pt as PPTPt



# ENVIRONMENT


load_dotenv()


def get_secret(name, default=None):
    """
    Read configuration from Streamlit Secrets first.

    Streamlit Cloud:
        Uses secrets configured in the Streamlit app.

    Local:
        Falls back to .env / environment variables.
    """

    try:
        value = st.secrets[name]

        if value is not None and str(value).strip():
            return str(value).strip()

    except Exception:
        pass

    value = os.getenv(name)

    if value is not None and str(value).strip():
        return str(value).strip()

    return default



# MAIN GROQ


GROQ_API_KEY = get_secret("GROQ_API_KEY")

GROQ_MODEL = get_secret(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)



# GROQ VISION


GROQ_VISION_API_KEY = get_secret(
    "GROQ_VISION_API_KEY"
)

GROQ_VISION_MODEL = get_secret(
    "GROQ_VISION_MODEL",
    "qwen/qwen3.8-27b",
)



# CLOUDFLARE IMAGE GENERATION


CLOUDFLARE_ACCOUNT_ID = get_secret(
    "CLOUDFLARE_ACCOUNT_ID"
)

CLOUDFLARE_API_TOKEN = get_secret(
    "CLOUDFLARE_API_TOKEN"
)

CLOUDFLARE_IMAGE_MODEL = (
    "@cf/black-forest-labs/flux-2-klein-4b"
)

IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024



# PAGE CONFIG


st.set_page_config(
    page_title="AI Library Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)



# CSS


st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #777;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .file-chip {
        display: inline-block;
        padding: 5px 10px;
        margin: 3px;
        border-radius: 12px;
        background: rgba(100,100,100,0.08);
        font-size: 0.82rem;
    }

    div[data-testid="stChatInput"] textarea {
        min-height: 80px !important;
        font-size: 16px !important;
        padding: 14px !important;
    }

    div[data-testid="stChatInput"] {
        width: 100% !important;
    }

    .creator-badge {
        width: fit-content;
        margin: 18px auto 8px auto;
        padding: 9px 20px;
        border-radius: 30px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #dbe3ef;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.08);
        display: flex;
        align-items: center;
        gap: 7px;
        animation: creatorFloat 3s ease-in-out infinite;
        transition: all 0.3s ease;
    }

    .creator-badge:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(15, 23, 42, 0.15);
        border-color: #b8c7dc;
    }

    .creator-label {
        color: #64748b;
        font-weight: 500;
        font-size: 0.82rem;
    }

    .creator-name {
        font-weight: 800;
        font-size: 0.86rem;
        background: linear-gradient(
            90deg,
            #2563eb,
            #7c3aed,
            #db2777,
            #2563eb
        );
        background-size: 300% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: colorFlow 4s linear infinite;
    }

    @keyframes colorFlow {
        0% {
            background-position: 0% center;
        }

        50% {
            background-position: 100% center;
        }

        100% {
            background-position: 0% center;
        }
    }

    @keyframes creatorFloat {
        0%, 100% {
            transform: translateY(0);
        }

        50% {
            transform: translateY(-2px);
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)



# SESSION STATE


def create_chat(title="New chat"):

    return {
        "title": title,
        "messages": [],
        "created": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),
        "attachment_context": "",
        "attachment_names": [],
    }


if "chats" not in st.session_state:

    st.session_state.chats = {
        "chat_1": create_chat("Getting started")
    }


if "current_chat_id" not in st.session_state:

    st.session_state.current_chat_id = "chat_1"


if "chat_counter" not in st.session_state:

    st.session_state.chat_counter = 1


if "generated_image" not in st.session_state:

    st.session_state.generated_image = None


if "generated_file" not in st.session_state:

    st.session_state.generated_file = None


def current_chat():

    return st.session_state.chats[
        st.session_state.current_chat_id
    ]


def chat_messages():

    return current_chat()["messages"]


def add_message(
    role,
    content,
    images=None,
):

    current_chat()["messages"].append(
        {
            "role": role,
            "content": content,
            "images": images or [],
        }
    )


def set_chat_title(title):

    if title:

        current_chat()["title"] = title[:55]


def new_chat():

    st.session_state.chat_counter += 1

    chat_id = (
        f"chat_{st.session_state.chat_counter}"
    )

    st.session_state.chats[chat_id] = create_chat(
        f"New chat {st.session_state.chat_counter}"
    )

    st.session_state.current_chat_id = chat_id

    st.session_state.generated_image = None
    st.session_state.generated_file = None



# MAIN GROQ LLM


@st.cache_resource
def get_llm():

    if not GROQ_API_KEY:

        return None

    return ChatGroq(
        model=GROQ_MODEL,
        groq_api_key=GROQ_API_KEY,
        temperature=0.2,
    )


def ask_groq(
    system_prompt,
    user_prompt,
):

    llm = get_llm()

    if llm is None:

        return (
            "GROQ_API_KEY is missing. "
            "Please configure it in Streamlit Secrets."
        )

    try:

        response = llm.invoke(
            [
                SystemMessage(
                    content=system_prompt
                ),
                HumanMessage(
                    content=user_prompt
                ),
            ]
        )

        return response.content

    except Exception as e:

        return (
            "Error while contacting Groq:\n\n"
            f"{type(e).__name__}: {str(e)}"
        )



# GROQ VISION


@st.cache_resource
def get_vision_client():

    if not GROQ_VISION_API_KEY:

        return None

    return Groq(
        api_key=GROQ_VISION_API_KEY
    )


def prepare_image_for_vision(image):

    if not isinstance(image, Image.Image):

        image = Image.open(image)

    image = ImageOps.exif_transpose(image)

    image = image.convert("RGB")

    max_dimension = 3000

    if (
        image.width > max_dimension
        or image.height > max_dimension
    ):

        image.thumbnail(
            (
                max_dimension,
                max_dimension,
            ),
            Image.Resampling.LANCZOS,
        )

    quality = 88

    while quality >= 55:

        buffer = BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=True,
        )

        image_bytes = buffer.getvalue()

        if len(image_bytes) < 15 * 1024 * 1024:

            break

        quality -= 5

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return (
        "data:image/jpeg;base64,"
        + encoded
    )


def ask_groq_vision(
    image,
    user_request,
):

    if not GROQ_VISION_API_KEY:

        return (
            False,
            (
                "GROQ_VISION_API_KEY is missing.\n\n"
                "Please configure your separate "
                "Groq Vision API key in "
                "Streamlit Secrets."
            ),
        )

    if not GROQ_VISION_MODEL:

        return (
            False,
            "GROQ_VISION_MODEL is missing.",
        )

    client = get_vision_client()

    if client is None:

        return (
            False,
            "Could not initialize the Groq Vision client.",
        )

    try:

        data_url = prepare_image_for_vision(
            image
        )

        prompt = f"""
You are the dedicated visual understanding
component of an AI Library Assistant.

Carefully inspect the uploaded image.

USER REQUEST:

{user_request}

Answer using only information actually visible
in the image.

You may:

- read text
- perform OCR
- describe the image
- explain a screenshot
- explain a chart or diagram
- analyze a photograph
- identify visible objects
- extract visible information
- answer questions about the image

Rules:

1. Do not invent missing information.
2. If text is blurry or unreadable, say so.
3. If asked what the image says, prioritize OCR.
4. Follow the user's current language automatically.
5. English -> English.
6. Urdu script -> Urdu script.
7. Roman Urdu -> Roman Urdu.
8. Mixed language -> naturally follow the user's style.
9. The uploaded image's language does not determine
   the answer language.
"""

        completion = (
            client.chat.completions.create(
                model=GROQ_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                },
                            },
                        ],
                    }
                ],
                temperature=0.7,
                max_completion_tokens=4096,
                top_p=0.8,
                stream=False,
            )
        )

        if (
            not completion
            or not completion.choices
        ):

            return (
                False,
                "Groq Vision returned no usable response.",
            )

        message = completion.choices[0].message

        answer = (
            message.content
            if message
            else None
        )

        if not answer:

            return (
                False,
                "Groq Vision returned an empty answer.",
            )

        return (
            True,
            answer.strip(),
        )

    except Exception as e:

        return (
            False,
            (
                f"Vision API error "
                f"({type(e).__name__}):\n\n"
                f"{str(e)}"
            ),
        )



# FILE TYPES


SUPPORTED_IMAGES = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
}

SUPPORTED_TEXT = {
    "txt",
    "md",
}

SUPPORTED_DOCUMENTS = {
    "pdf",
    "docx",
    "pptx",
    "xlsx",
    "xlsm",
    "csv",
}


def get_extension(filename):

    if "." not in filename:

        return ""

    return filename.lower().rsplit(
        ".",
        1,
    )[-1]


def is_image_file(filename):

    return (
        get_extension(filename)
        in SUPPORTED_IMAGES
    )



# CATALOG


CATALOG_FILES = [
    "library_catalog.csv",
    "catalog.csv",
    "books.csv",
]


@st.cache_data
def load_catalog():

    for filename in CATALOG_FILES:

        if os.path.exists(filename):

            try:

                return pd.read_csv(
                    filename
                )

            except Exception:

                continue

    return None


def search_catalog(query):

    df = load_catalog()

    if df is None:

        return None

    if not query.strip():

        return df.head(20)

    mask = pd.Series(
        False,
        index=df.index,
    )

    query_lower = query.lower()

    for column in df.columns:

        values = (
            df[column]
            .fillna("")
            .astype(str)
            .str.lower()
        )

        mask = (
            mask
            | values.str.contains(
                query_lower,
                regex=False,
            )
        )

    return df[mask].head(20)



# FILE EXTRACTION


def extract_pdf(file):

    reader = PdfReader(
        BytesIO(file.getvalue())
    )

    pages = []

    for page in reader.pages:

        try:

            pages.append(
                page.extract_text() or ""
            )

        except Exception:

            pass

    return "\n".join(pages)


def extract_docx(file):

    document = Document(
        BytesIO(file.getvalue())
    )

    parts = []

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:

            parts.append(text)

    return "\n".join(parts)


def extract_pptx(file):

    presentation = Presentation(
        BytesIO(file.getvalue())
    )

    slides = []

    for index, slide in enumerate(
        presentation.slides,
        start=1,
    ):

        slide_text = [
            f"SLIDE {index}"
        ]

        for shape in slide.shapes:

            if hasattr(shape, "text"):

                text = shape.text.strip()

                if text:

                    slide_text.append(text)

        slides.append(
            "\n".join(slide_text)
        )

    return "\n\n".join(slides)


def extract_excel(file):

    workbook = load_workbook(
        filename=BytesIO(
            file.getvalue()
        ),
        read_only=True,
        data_only=True,
    )

    output = []

    for sheet_name in workbook.sheetnames:

        sheet = workbook[sheet_name]

        output.append(
            f"SHEET: {sheet_name}"
        )

        rows = []

        for row in sheet.iter_rows(
            values_only=True
        ):

            values = [
                ""
                if value is None
                else str(value)
                for value in row
            ]

            if any(values):

                rows.append(
                    " | ".join(values)
                )

        output.extend(rows[:1000])

    return "\n".join(output)


def extract_csv(file):

    try:

        df = pd.read_csv(
            BytesIO(file.getvalue())
        )

        return df.to_string(
            index=False
        )

    except Exception as e:

        return (
            "Could not read CSV: "
            f"{str(e)}"
        )


def extract_text_file(file):

    raw = file.getvalue()

    for encoding in [
        "utf-8",
        "utf-16",
        "latin-1",
    ]:

        try:

            return raw.decode(
                encoding
            )

        except Exception:

            continue

    return "Could not decode text file."



# ATTACHMENT PROCESSING


def process_uploaded_file(
    file,
    user_request,
):

    filename = file.name

    extension = get_extension(
        filename
    )

    if extension in SUPPORTED_IMAGES:

        try:

            image = Image.open(
                BytesIO(file.getvalue())
            )

            success, result = (
                ask_groq_vision(
                    image,
                    user_request
                    or
                    "Analyze this image carefully.",
                )
            )

            return (
                f"IMAGE: {filename}\n\n"
                f"{result}"
            )

        except Exception as e:

            return (
                f"IMAGE: {filename}\n\n"
                "Could not process image:\n\n"
                f"{type(e).__name__}: "
                f"{str(e)}"
            )

    if extension == "pdf":

        return (
            f"FILE: {filename}\n\n"
            + extract_pdf(file)
        )

    if extension == "docx":

        return (
            f"FILE: {filename}\n\n"
            + extract_docx(file)
        )

    if extension == "pptx":

        return (
            f"FILE: {filename}\n\n"
            + extract_pptx(file)
        )

    if extension in {
        "xlsx",
        "xlsm",
    }:

        return (
            f"FILE: {filename}\n\n"
            + extract_excel(file)
        )

    if extension == "csv":

        return (
            f"FILE: {filename}\n\n"
            + extract_csv(file)
        )

    if extension in SUPPORTED_TEXT:

        return (
            f"FILE: {filename}\n\n"
            + extract_text_file(file)
        )

    return (
        f"FILE: {filename}\n\n"
        "This file type is not currently "
        "supported for direct extraction."
    )


def process_uploaded_files(
    files,
    user_request,
):

    if not files:

        return "", [], []

    contexts = []
    names = []
    uploaded_images = []

    for file in files:

        names.append(file.name)

        if is_image_file(file.name):

            try:

                image_bytes = file.getvalue()

                Image.open(
                    BytesIO(image_bytes)
                ).verify()

                uploaded_images.append(
                    {
                        "name": file.name,
                        "data": image_bytes,
                    }
                )

            except Exception:

                pass

        contexts.append(
            process_uploaded_file(
                file,
                user_request,
            )
        )

    combined = "\n\n".join(contexts)

    combined = combined[:120000]

    return (
        combined,
        names,
        uploaded_images,
    )



# SYSTEM PROMPT


LIBRARY_SYSTEM_PROMPT = """
You are an intelligent AI Library Assistant.

You support:

- students
- researchers
- librarians
- teachers
- university users
- general library users

You can help with:

- library questions
- research assistance
- literature searching
- information literacy
- citations
- summarization
- cataloguing
- academic writing
- document analysis
- image understanding
- library services
- learning

LANGUAGE:

Automatically detect the language and writing
style of the user's CURRENT request.

English -> English.

Urdu script -> Urdu script.

Roman Urdu -> Roman Urdu.

Mixed English/Urdu -> naturally follow the user's style.

If the user explicitly asks for another language,
follow that instruction.

Never force the language of an uploaded document
onto the answer language.

LIBRARY ACCURACY:

Do not fabricate:

- books
- authors
- ISBNs
- publishers
- citations
- catalog records
- availability

Clearly distinguish verified catalog information
from general knowledge.

ACADEMIC QUALITY:

Use headings, bullets, numbered steps, examples
and tables when useful.

Keep explanations understandable.

Maintain conversation context.
"""



# CHAT HISTORY


def get_history():

    recent = chat_messages()[-12:]

    history_parts = []

    for message in recent:

        history_parts.append(
            f"""
{message["role"].upper()}:

{message["content"]}
"""
        )

    return "\n".join(
        history_parts
    )



# IMAGE GENERATION INTENT


def looks_like_image_generation_request(text):
    """
    Detect natural-language image generation requests.

    Examples recognized:

    generate an image
    generate me an image
    generate an image of a library
    create me a picture
    make an image of...
    make me a picture
    draw me...
    can you create an image...
    I want an image of...
    show me an image of...
    generate artwork...
    create a poster...
    visualize...
    """

    if not text:
        return False

    text_lower = re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )

    # Direct image-generation actions.
    action_patterns = [
        r"\b(generate|create|make|draw|design|produce|render)\b"
        r".{0,40}"
        r"\b(image|picture|photo|artwork|illustration|visual|poster)\b",

        r"\b(image|picture|photo|artwork|illustration|visual|poster)\b"
        r".{0,40}"
        r"\b(generate|create|make|draw|design|produce|render)\b",
    ]

    for pattern in action_patterns:

        if re.search(
            pattern,
            text_lower,
            flags=re.IGNORECASE,
        ):

            return True

    # Direct requests such as:
    # "show me an image of..."
    if re.search(
        r"\b(show|give|provide)\b"
        r".{0,30}"
        r"\b(an?\s+)?"
        r"(image|picture|photo|visual)\b",
        text_lower,
    ):

        return True

    # "I want an image of..."
    if re.search(
        r"\b(i want|i need|i would like|i'd like)\b"
        r".{0,30}"
        r"\b(an?\s+)?"
        r"(image|picture|photo|visual|artwork)\b",
        text_lower,
    ):

        return True

    # "visualize..."
    if re.search(
        r"\bvisuali[sz]e\b",
        text_lower,
    ):

        return True

    # "draw me..."
    if re.search(
        r"\bdraw\s+(me\s+)?",
        text_lower,
    ) and any(
        word in text_lower
        for word in [
            "image",
            "picture",
            "person",
            "scene",
            "library",
            "book",
            "poster",
            "art",
        ]
    ):

        return True

    # Poster-specific requests.
    if re.search(
        r"\b(create|make|design|generate)\b"
        r".{0,30}"
        r"\bposter\b",
        text_lower,
    ):

        return True

    # Artwork-specific requests.
    if re.search(
        r"\b(create|make|generate|draw|design)\b"
        r".{0,30}"
        r"\bartwork\b",
        text_lower,
    ):

        return True

    return False



# FILE GENERATION INTENT


def detect_file_format(text):

    if not text:
        return None

    text_lower = text.lower()

    # PowerPoint
    if any(
        phrase in text_lower
        for phrase in [
            "powerpoint",
            "pptx",
            "presentation",
            "slide deck",
            "slides",
        ]
    ):

        return "pptx"

    # PDF
    if any(
        phrase in text_lower
        for phrase in [
            "pdf",
            "portable document",
        ]
    ):

        return "pdf"

    # Word
    if any(
        phrase in text_lower
        for phrase in [
            "word file",
            "word document",
            "docx",
            ".docx",
        ]
    ):

        return "docx"

    # Excel
    if any(
        phrase in text_lower
        for phrase in [
            "excel",
            "xlsx",
            "spreadsheet",
            ".xlsx",
        ]
    ):

        return "xlsx"

    # CSV
    if any(
        phrase in text_lower
        for phrase in [
            "csv",
            "comma separated",
        ]
    ):

        return "csv"

    # Markdown
    if any(
        phrase in text_lower
        for phrase in [
            "markdown",
            ".md",
            "md file",
        ]
    ):

        return "md"

    # Text
    if any(
        phrase in text_lower
        for phrase in [
            "text file",
            "txt file",
            ".txt",
        ]
    ):

        return "txt"

    # Report -> PDF
    if any(
        phrase in text_lower
        for phrase in [
            "downloadable report",
            "generate a report",
            "create a report",
            "prepare a report",
            "make a report",
        ]
    ):

        return "pdf"

    return None


def looks_like_file_generation_request(text):

    if not text:
        return False

    text_lower = re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )

    requested_format = detect_file_format(
        text
    )

    # --------------------------------------------------------
    # Explicit file actions
    # --------------------------------------------------------

    action_patterns = [
        r"\b(generate|create|prepare|make|export|download|save|convert|build)\b",
        r"\b(turn|convert)\b",
    ]

    has_action = any(
        re.search(
            pattern,
            text_lower,
        )
        for pattern in action_patterns
    )

    # --------------------------------------------------------
    # File-related words
    # --------------------------------------------------------

    file_words = [
        "file",
        "document",
        "report",
        "presentation",
        "slides",
        "slide deck",
        "spreadsheet",
        "excel",
        "word",
        "pdf",
        "powerpoint",
        "pptx",
        "docx",
        "xlsx",
        "csv",
        "markdown",
        "text file",
        "downloadable",
    ]

    has_file_word = any(
        word in text_lower
        for word in file_words
    )

    # --------------------------------------------------------
    # If there is a recognized format, require an action.
    #
    # This prevents:
    #
    # "What is a PDF?"
    # "Explain Excel"
    # "What is PowerPoint?"
    #
    # from generating files.
    # --------------------------------------------------------

    if requested_format:

        return has_action

    # --------------------------------------------------------
    # Natural file requests without explicit extension.
    #
    # Examples:
    #
    # "make me a document"
    # "create a downloadable file"
    # "prepare a report"
    # "make me a presentation"
    # --------------------------------------------------------

    if has_action and has_file_word:

        return True

    return False



# INTENT DETECTION


def detect_intent(text):

    text_lower = text.lower()

    # --------------------------------------------------------
    # IMAGE GENERATION FIRST
    # --------------------------------------------------------
    #
    # This is intentionally checked before normal questions
    # and before uploaded-image analysis.
    #
    # Example:
    #
    # "generate me an image of a person searching for books"
    #
    # -> IMAGE_GENERATION
    #
    # --------------------------------------------------------

    if looks_like_image_generation_request(
        text
    ):

        return "IMAGE_GENERATION"

    # --------------------------------------------------------
    # FILE GENERATION
    # --------------------------------------------------------

    if looks_like_file_generation_request(
        text
    ):

        return "FILE_GENERATION"

    # --------------------------------------------------------
    # CATALOG
    # --------------------------------------------------------

    if any(
        word in text_lower
        for word in [
            "catalog",
            "isbn",
            "book availability",
            "find book",
            "search book",
        ]
    ):

        return "CATALOG_SEARCH"

    # --------------------------------------------------------
    # SUMMARIZATION
    # --------------------------------------------------------

    if any(
        word in text_lower
        for word in [
            "summarize",
            "summary",
            "summarise",
        ]
    ):

        return "SUMMARIZER"

    # --------------------------------------------------------
    # CITATIONS
    # --------------------------------------------------------

    if any(
        word in text_lower
        for word in [
            "citation",
            "reference",
            "apa",
            "mla",
            "chicago",
        ]
    ):

        return "CITATION_ASSISTANT"

    # --------------------------------------------------------
    # CATALOGUING
    # --------------------------------------------------------

    if any(
        word in text_lower
        for word in [
            "cataloguing",
            "cataloging",
            "classification",
            "ddc",
            "metadata",
        ]
    ):

        return "CATALOGUING_ASSISTANT"

    # --------------------------------------------------------
    # INFORMATION LITERACY
    # --------------------------------------------------------

    if any(
        word in text_lower
        for word in [
            "information literacy",
            "evaluate source",
            "credible source",
            "reliable source",
        ]
    ):

        return "INFORMATION_LITERACY"

    # --------------------------------------------------------
    # RESEARCH
    # --------------------------------------------------------

    if any(
        word in text_lower
        for word in [
            "research",
            "literature review",
            "research paper",
            "academic research",
        ]
    ):

        return "RESEARCH_ASSISTANT"

    # --------------------------------------------------------
    # WRITING
    # --------------------------------------------------------

    if any(
        word in text_lower
        for word in [
            "essay",
            "rewrite",
            "write",
            "grammar",
            "proofread",
        ]
    ):

        return "WRITING_ASSISTANT"

    # --------------------------------------------------------
    # GENERAL
    # --------------------------------------------------------

    return "GENERAL_LIBRARY"



# NORMAL LIBRARY ANSWER


def answer_library_question(
    user_request,
    intent,
    attachment_context="",
):

    specialized_instruction = ""

    if intent == "RESEARCH_ASSISTANT":

        specialized_instruction = """
Focus on research methodology, search strategies,
academic databases, literature review techniques,
source evaluation, and research planning.
"""

    elif intent == "SUMMARIZER":

        specialized_instruction = """
Summarize the provided material accurately.
Preserve important concepts, findings,
arguments and conclusions.
"""

    elif intent == "CITATION_ASSISTANT":

        specialized_instruction = """
Help with citations and references.
Do not invent bibliographic information.
"""

    elif intent == "CATALOGUING_ASSISTANT":

        specialized_instruction = """
Focus on cataloguing, metadata, classification,
subject headings, DDC, MARC concepts,
and bibliographic description.
"""

    elif intent == "INFORMATION_LITERACY":

        specialized_instruction = """
Focus on source evaluation, credibility,
authority, relevance, bias, evidence,
and search strategies.
"""

    elif intent == "WRITING_ASSISTANT":

        specialized_instruction = """
Help the user write clearly and appropriately
for their requested audience.
"""

    elif intent == "CATALOG_SEARCH":

        specialized_instruction = """
If catalog data is available, treat it as the
authoritative source for catalog-specific
information.
"""

    prompt = f"""
{specialized_instruction}

CURRENT USER REQUEST:

{user_request}

CONVERSATION HISTORY:

{get_history()}

UPLOADED MATERIAL:

{
    attachment_context
    if attachment_context
    else
    "No attachment provided."
}

Answer the user directly.

If the user asks for an explanation, explain it.

If the user asks to analyze a file, analyze it.

If the user asks for a summary, summarize it.

Respect the user's language automatically.
"""

    return ask_groq(
        LIBRARY_SYSTEM_PROMPT,
        prompt,
    )



# IMAGE GENERATION


def create_image_prompt(
    user_request
):

    system = """
You are the internal prompt-writing component
of an AI image generation system.

Convert the user's image request into a detailed
image-generation prompt.

Include only useful visual information such as:

- subject
- environment
- composition
- visual style
- lighting
- mood
- important objects
- perspective
- camera framing
- realism or artistic style when appropriate

Preserve the user's intended subject and meaning.

Do not answer the user.

Do not explain anything.

Return ONLY the final image-generation prompt.
"""

    return ask_groq(
        system,
        user_request,
    )


def generate_image(
    user_request
):

    if not CLOUDFLARE_ACCOUNT_ID:

        return (
            None,
            "CLOUDFLARE_ACCOUNT_ID is missing.",
        )

    if not CLOUDFLARE_API_TOKEN:

        return (
            None,
            "CLOUDFLARE_API_TOKEN is missing.",
        )

    try:

        # Groq is used internally only to improve
        # the image prompt. The user never sees
        # this prompt.
        prompt = create_image_prompt(
            user_request
        )

        # If Groq itself returned an error,
        # don't send that error as the image prompt.
        if (
            not prompt
            or prompt.startswith(
                "Error while contacting Groq:"
            )
            or prompt.startswith(
                "GROQ_API_KEY is missing"
            )
        ):

            return (
                None,
                prompt
                or "Could not create the image prompt.",
            )

        url = (
            "https://api.cloudflare.com/client/v4/"
            f"accounts/{CLOUDFLARE_ACCOUNT_ID}"
            f"/ai/run/{CLOUDFLARE_IMAGE_MODEL}"
        )

        headers = {
            "Authorization": (
                f"Bearer {CLOUDFLARE_API_TOKEN}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "width": IMAGE_WIDTH,
            "height": IMAGE_HEIGHT,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=180,
        )

        response.raise_for_status()

        result = response.json()

        if not result.get("success"):

            return (
                None,
                str(result),
            )

        image_data = (
            result
            .get("result", {})
            .get("image")
        )

        if not image_data:

            return (
                None,
                "Cloudflare returned no image.",
            )

        image_bytes = base64.b64decode(
            image_data
        )

        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

        return (
            image,
            None,
        )

    except Exception as e:

        return (
            None,
            (
                f"{type(e).__name__}: "
                f"{str(e)}"
            ),
        )



# FILE GENERATION HELPERS


def clean_markdown_for_text(
    text
):

    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"\1",
        text,
    )

    text = re.sub(
        r"\*(.*?)\*",
        r"\1",
        text,
    )

    text = re.sub(
        r"`(.*?)`",
        r"\1",
        text,
    )

    return text.strip()


def generate_docx(
    content
):

    document = Document()

    document.add_heading(
        "AI Library Assistant",
        level=0,
    )

    document.add_paragraph(
        datetime.now().strftime(
            "%Y-%m-%d"
        )
    )

    for line in content.splitlines():

        line = line.strip()

        if not line:

            continue

        if line.startswith("# "):

            document.add_heading(
                line[2:].strip(),
                level=1,
            )

        elif line.startswith("## "):

            document.add_heading(
                line[3:].strip(),
                level=2,
            )

        elif line.startswith("### "):

            document.add_heading(
                line[4:].strip(),
                level=3,
            )

        elif line.startswith("- "):

            document.add_paragraph(
                line[2:].strip(),
                style="List Bullet",
            )

        elif re.match(
            r"^\d+\.\s+",
            line,
        ):

            clean = re.sub(
                r"^\d+\.\s+",
                "",
                line,
            )

            document.add_paragraph(
                clean,
                style="List Number",
            )

        else:

            document.add_paragraph(
                clean_markdown_for_text(
                    line
                )
            )

    for paragraph in document.paragraphs:

        for run in paragraph.runs:

            run.font.size = Pt(11)

    output = BytesIO()

    document.save(output)

    return output.getvalue()


def generate_pdf(
    content
):

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        "LibraryBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "LibraryHeading",
        parent=styles["Heading2"],
        fontSize=15,
        leading=19,
        spaceBefore=12,
        spaceAfter=8,
    )

    story = []

    for line in content.splitlines():

        line = line.strip()

        if not line:

            story.append(
                Spacer(1, 6)
            )

            continue

        if line.startswith("#"):

            heading = re.sub(
                r"^#+\s*",
                "",
                line,
            )

            story.append(
                Paragraph(
                    html.escape(heading),
                    heading_style,
                )
            )

        elif line.startswith("- "):

            bullet = (
                "• "
                + html.escape(
                    line[2:].strip()
                )
            )

            story.append(
                Paragraph(
                    bullet,
                    body_style,
                )
            )

        else:

            clean = clean_markdown_for_text(
                line
            )

            story.append(
                Paragraph(
                    html.escape(clean),
                    body_style,
                )
            )

    document.build(story)

    return output.getvalue()


def parse_markdown_table(
    content
):

    lines = [
        line.strip()
        for line in content.splitlines()
        if "|" in line
    ]

    if len(lines) < 2:

        return None

    rows = []

    for line in lines:

        if re.match(
            r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$",
            line,
        ):

            continue

        cells = [
            cell.strip()
            for cell in
            line.strip("|").split("|")
        ]

        rows.append(cells)

    if len(rows) < 2:

        return None

    columns = rows[0]

    data_rows = []

    for row in rows[1:]:

        if len(row) < len(columns):

            row += [
                ""
                for _ in range(
                    len(columns) - len(row)
                )
            ]

        data_rows.append(
            row[:len(columns)]
        )

    return (
        columns,
        data_rows,
    )


def generate_xlsx(
    content
):

    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Library Data"

    table = parse_markdown_table(
        content
    )

    if table:

        columns, rows = table

        sheet.append(columns)

        for row in rows[:500]:

            sheet.append(row)

    else:

        sheet.append(
            ["Content"]
        )

        for line in content.splitlines():

            line = line.strip()

            if line:

                sheet.append(
                    [
                        clean_markdown_for_text(
                            line
                        )
                    ]
                )

    for column in sheet.columns:

        max_length = 0

        column_letter = (
            column[0].column_letter
        )

        for cell in column:

            if cell.value is not None:

                max_length = max(
                    max_length,
                    len(str(cell.value)),
                )

        sheet.column_dimensions[
            column_letter
        ].width = min(
            max_length + 2,
            50,
        )

    output = BytesIO()

    workbook.save(output)

    return output.getvalue()


def generate_csv(
    content
):

    table = parse_markdown_table(
        content
    )

    if table:

        columns, rows = table

        df = pd.DataFrame(
            rows,
            columns=columns,
        )

    else:

        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        df = pd.DataFrame(
            {
                "Content": lines
            }
        )

    return df.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )


def generate_txt(
    content
):

    return clean_markdown_for_text(
        content
    ).encode("utf-8")


def generate_markdown(
    content
):

    return content.encode(
        "utf-8"
    )



# POWERPOINT


def generate_presentation_structure(
    user_request,
    content,
    attachment_context="",
):

    system = """
Create a PowerPoint presentation structure.

Return ONLY valid JSON.

Format:

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

Create a logical presentation.

Do not use markdown.

Do not include speaker notes.

Keep slides concise.
"""

    prompt = f"""
USER REQUEST:

{user_request}

CONTENT:

{content}

UPLOADED MATERIAL:

{attachment_context[:30000]}

Create the presentation structure.
"""

    response = ask_groq(
        system,
        prompt,
    )

    try:

        response = response.strip()

        response = re.sub(
            r"^```json\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"```$",
            "",
            response,
        )

        return json.loads(
            response.strip()
        )

    except Exception:

        return {
            "title": user_request[:80],
            "slides": [
                {
                    "title": "Overview",
                    "bullets": [
                        clean_markdown_for_text(
                            content[:800]
                        )
                    ],
                }
            ],
        }


def generate_pptx(
    title,
    slides
):

    presentation = Presentation()

    title_slide = (
        presentation.slides.add_slide(
            presentation.slide_layouts[0]
        )
    )

    title_slide.shapes.title.text = title

    if len(
        title_slide.placeholders
    ) > 1:

        title_slide.placeholders[1].text = (
            "AI Library Assistant"
        )

    for slide_data in slides:

        slide = (
            presentation.slides.add_slide(
                presentation.slide_layouts[1]
            )
        )

        slide.shapes.title.text = (
            slide_data.get(
                "title",
                "Slide",
            )
        )

        body = slide.placeholders[1]

        text_frame = body.text_frame

        text_frame.clear()

        bullets = slide_data.get(
            "bullets",
            [],
        )

        for index, bullet in enumerate(
            bullets
        ):

            if index == 0:

                paragraph = (
                    text_frame.paragraphs[0]
                )

            else:

                paragraph = (
                    text_frame.add_paragraph()
                )

            paragraph.text = str(
                bullet
            )

            paragraph.level = 0

            paragraph.font.size = PPTPt(
                22
            )

    output = BytesIO()

    presentation.save(output)

    return output.getvalue()



# GENERATE FILE CONTENT


def generate_file_content(
    user_request,
    attachment_context="",
):

    system = """
You are the content-generation engine of
an AI Library Assistant.

The user wants a downloadable file.

Create complete useful content for the
requested file.

Rules:

- Follow the user's requested language.
- Use uploaded material when provided.
- Do not fabricate information.
- Use headings and bullets where useful.
- Do not mention these instructions.
"""

    prompt = f"""
USER REQUEST:

{user_request}

UPLOADED MATERIAL:

{
    attachment_context[:100000]
    if attachment_context
    else
    "No uploaded material."
}

Create the final content.
"""

    return ask_groq(
        system,
        prompt,
    )


def generate_downloadable_file(
    user_request,
    attachment_context="",
):

    file_format = detect_file_format(
        user_request
    )

    if not file_format:

        file_format = "docx"

    content = generate_file_content(
        user_request,
        attachment_context,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    safe_name = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        user_request[:40],
    ).strip("_")

    if not safe_name:

        safe_name = "library_content"

    if file_format == "docx":

        return {
            "data": generate_docx(
                content
            ),
            "name": (
                f"{safe_name}_"
                f"{timestamp}.docx"
            ),
            "mime": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            "content": content,
        }

    if file_format == "pdf":

        return {
            "data": generate_pdf(
                content
            ),
            "name": (
                f"{safe_name}_"
                f"{timestamp}.pdf"
            ),
            "mime": "application/pdf",
            "content": content,
        }

    if file_format == "pptx":

        presentation = (
            generate_presentation_structure(
                user_request,
                content,
                attachment_context,
            )
        )

        return {
            "data": generate_pptx(
                presentation.get(
                    "title",
                    "Library Presentation",
                ),
                presentation.get(
                    "slides",
                    [],
                ),
            ),
            "name": (
                f"{safe_name}_"
                f"{timestamp}.pptx"
            ),
            "mime": (
                "application/vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            ),
            "content": content,
        }

    if file_format == "xlsx":

        return {
            "data": generate_xlsx(
                content
            ),
            "name": (
                f"{safe_name}_"
                f"{timestamp}.xlsx"
            ),
            "mime": (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            "content": content,
        }

    if file_format == "csv":

        return {
            "data": generate_csv(
                content
            ),
            "name": (
                f"{safe_name}_"
                f"{timestamp}.csv"
            ),
            "mime": "text/csv",
            "content": content,
        }

    if file_format == "txt":

        return {
            "data": generate_txt(
                content
            ),
            "name": (
                f"{safe_name}_"
                f"{timestamp}.txt"
            ),
            "mime": "text/plain",
            "content": content,
        }

    if file_format == "md":

        return {
            "data": generate_markdown(
                content
            ),
            "name": (
                f"{safe_name}_"
                f"{timestamp}.md"
            ),
            "mime": "text/markdown",
            "content": content,
        }

    return None



# COPY BUTTON


def copy_button(
    text,
    button_id,
):

    safe_text = json.dumps(
        text,
        ensure_ascii=False,
    )

    html_block = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <style>

            html,
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }}

            .copy-container {{
                display: flex;
                align-items: center;
                height: 42px;
            }}

            button {{
                border: 1px solid #d1d5db;
                background: white;
                color: #374151;
                border-radius: 8px;
                padding: 7px 13px;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s ease;
            }}

            button:hover {{
                background: #f3f4f6;
                border-color: #9ca3af;
            }}

            button:active {{
                transform: scale(0.97);
            }}

        </style>

    </head>

    <body>

        <div class="copy-container">

            <button
                id="{button_id}"
                onclick="copyText()"
            >
                📋 Copy
            </button>

        </div>

        <script>

            const textToCopy = {safe_text};

            async function copyText() {{

                const button =
                    document.getElementById(
                        "{button_id}"
                    );

                try {{

                    await navigator.clipboard
                        .writeText(
                            textToCopy
                        );

                    button.innerText =
                        "✓ Copied";

                    setTimeout(
                        () => {{
                            button.innerText =
                                "📋 Copy";
                        }},
                        1500
                    );

                }} catch (error) {{

                    button.innerText =
                        "Copy failed";

                    setTimeout(
                        () => {{
                            button.innerText =
                                "📋 Copy";
                        }},
                        1500
                    );

                }}

            }}

        </script>

    </body>

    </html>
    """

    st.iframe(
        html_block,
        height=45,
    )



# SIDEBAR


with st.sidebar:

    st.markdown(
        "## 📚 AI Library Assistant"
    )

    if st.button(
        "＋ New Chat",
        use_container_width=True,
    ):

        new_chat()

        st.rerun()

    st.markdown("---")

    st.markdown(
        "### 💬 Chat History"
    )

    for (
        chat_id,
        chat,
    ) in reversed(
        list(
            st.session_state.chats.items()
        )
    ):

        label = chat["title"]

        if len(label) > 35:

            label = (
                label[:35]
                + "..."
            )

        if st.button(
            label,
            key=f"chat_{chat_id}",
            use_container_width=True,
        ):

            st.session_state.current_chat_id = (
                chat_id
            )

            st.session_state.generated_image = (
                None
            )

            st.session_state.generated_file = (
                None
            )

            st.rerun()

    st.markdown("---")

    current = current_chat()

    if current["messages"]:

        if st.button(
            "🧹 Clear Current Chat",
            use_container_width=True,
        ):

            current["messages"] = []

            current[
                "attachment_context"
            ] = ""

            current[
                "attachment_names"
            ] = []

            st.session_state.generated_image = (
                None
            )

            st.session_state.generated_file = (
                None
            )

            st.rerun()

    if len(
        st.session_state.chats
    ) > 1:

        if st.button(
            "🗑️ Delete Current Chat",
            use_container_width=True,
        ):

            current_id = (
                st.session_state.current_chat_id
            )

            del st.session_state.chats[
                current_id
            ]

            st.session_state.current_chat_id = (
                next(
                    iter(
                        st.session_state.chats
                    )
                )
            )

            st.session_state.generated_image = (
                None
            )

            st.session_state.generated_file = (
                None
            )

            st.rerun()



# HEADER


st.markdown(
    """
    <div class="main-title">
        📚 AI Library Assistant
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        Your intelligent assistant for library research,
        documents, images, academic work, and learning.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="creator-badge">
        <span class="creator-label">Created by</span>
        <span class="creator-name">Hafiz Subhan Amir</span>
    </div>

    <style>
    .creator-badge {
        width: fit-content;
        margin: 18px auto 8px auto;
        padding: 9px 20px;
        border-radius: 30px;

        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #dbe3ef;

        box-shadow:
            0 4px 15px rgba(15, 23, 42, 0.08);

        display: flex;
        align-items: center;
        gap: 7px;

        animation: creatorFloat 3s ease-in-out infinite;
        transition: all 0.3s ease;
    }

    .creator-badge:hover {
        transform: translateY(-3px) scale(1.02);

        box-shadow:
            0 8px 25px rgba(15, 23, 42, 0.15);

        border-color: #b8c7dc;
    }

    .creator-label {
        color: #64748b;
        font-weight: 500;
        font-size: 0.82rem;
    }

    .creator-name {
        font-weight: 800;
        font-size: 0.86rem;

        background: linear-gradient(
            90deg,
            #2563eb,
            #7c3aed,
            #db2777,
            #2563eb
        );

        background-size: 300% auto;

        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;

        background-clip: text;

        animation: colorFlow 4s linear infinite;
    }

    @keyframes colorFlow {
        0% {
            background-position: 0% center;
        }

        50% {
            background-position: 100% center;
        }

        100% {
            background-position: 0% center;
        }
    }

    @keyframes creatorFloat {
        0%, 100% {
            transform: translateY(0);
        }

        50% {
            transform: translateY(-2px);
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)



# CURRENT ATTACHMENTS


if current_chat()["attachment_names"]:

    names_html = " ".join(
        [
            (
                '<span class="file-chip">'
                f'📎 {html.escape(name)}'
                "</span>"
            )
            for name in
            current_chat()[
                "attachment_names"
            ]
        ]
    )

    st.markdown(
        names_html,
        unsafe_allow_html=True,
    )



# DISPLAY CHAT


for index, message in enumerate(
    chat_messages()
):

    role = message["role"]

    content = message["content"]

    with st.chat_message(role):

        st.markdown(content)

        message_images = message.get(
            "images",
            [],
        )

        if message_images:

            for image_data in message_images:

                try:

                    image = Image.open(
                        BytesIO(
                            image_data["data"]
                        )
                    )

                    st.image(
                        image,
                        caption=image_data[
                            "name"
                        ],
                        width=500,
                    )

                except Exception as e:

                    st.warning(
                        "Could not display "
                        f"{image_data.get('name', 'image')}: "
                        f"{str(e)}"
                    )

        if role == "assistant":

            copy_button(
                content,
                f"copy_{index}",
            )



# GENERATED IMAGE


if st.session_state.generated_image:

    st.markdown(
        "### 🖼️ Generated Image"
    )

    st.image(
        st.session_state.generated_image,
        use_container_width=True,
    )

    image_buffer = BytesIO()

    st.session_state.generated_image.save(
        image_buffer,
        format="PNG",
    )

    st.download_button(
        "⬇️ Download Image",
        data=image_buffer.getvalue(),
        file_name=(
            "library_generated_image.png"
        ),
        mime="image/png",
        use_container_width=True,
    )



# GENERATED FILE


if st.session_state.generated_file:

    generated_file = (
        st.session_state.generated_file
    )

    st.markdown(
        "### 📥 Your Downloadable File"
    )

    st.download_button(
        (
            "⬇️ Download "
            f"{generated_file['name']}"
        ),
        data=generated_file["data"],
        file_name=generated_file["name"],
        mime=generated_file["mime"],
        use_container_width=True,
    )



# CHAT INPUT


chat_input = st.chat_input(
    (
        "Ask anything about libraries, "
        "research, documents, or learning..."
    ),
    accept_file="multiple",
    file_type=[
        "pdf",
        "docx",
        "pptx",
        "xlsx",
        "xlsm",
        "csv",
        "txt",
        "md",
        "jpg",
        "jpeg",
        "png",
        "webp",
        "gif",
    ],
    max_upload_size=20,
)



# PROCESS USER REQUEST


if chat_input:

    user_request = (
        chat_input.text.strip()
        if chat_input.text
        else ""
    )

    uploaded_files = (
        chat_input.files
        if hasattr(
            chat_input,
            "files",
        )
        else []
    )

    if (
        not user_request
        and uploaded_files
    ):

        user_request = (
            "Please analyze the uploaded "
            "file(s) and explain what they contain."
        )

    attachment_context = ""

    attachment_names = []

    uploaded_images = []

    if uploaded_files:

        with st.spinner(
            "Reading your file(s)..."
        ):

            (
                attachment_context,
                attachment_names,
                uploaded_images,
            ) = process_uploaded_files(
                uploaded_files,
                user_request,
            )

        current_chat()[
            "attachment_context"
        ] = attachment_context

        current_chat()[
            "attachment_names"
        ] = attachment_names

    else:

        attachment_context = (
            current_chat()[
                "attachment_context"
            ]
        )

    display_user_message = (
        user_request
    )

    if attachment_names:

        display_user_message += (
            "\n\n📎 **Attached:** "
            + ", ".join(
                attachment_names
            )
        )

    add_message(
        "user",
        display_user_message,
        images=uploaded_images,
    )

    if len(chat_messages()) <= 1:

        set_chat_title(
            user_request
        )

    # ========================================================
    # DETECT INTENT
    # ========================================================

    intent = detect_intent(
        user_request
    )


    # ========================================================
    # FILE GENERATION
    # ========================================================

    if intent == "FILE_GENERATION":

        with st.spinner(
            "Preparing your downloadable file..."
        ):

            try:

                generated = (
                    generate_downloadable_file(
                        user_request,
                        attachment_context,
                    )
                )

                if generated:

                    st.session_state.generated_file = (
                        generated
                    )

                    st.session_state.generated_image = (
                        None
                    )

                    assistant_message = (
                        "I prepared the requested "
                        f"**{generated['name'].split('.')[-1].upper()} "
                        "file**.\n\n"
                        "You can download it below."
                    )

                else:

                    assistant_message = (
                        "I couldn't determine the "
                        "requested file format."
                    )

            except Exception as e:

                assistant_message = (
                    "File generation failed:\n\n"
                    f"{type(e).__name__}: "
                    f"{str(e)}"
                )

        add_message(
            "assistant",
            assistant_message,
        )

        st.rerun()


    # ========================================================
    # IMAGE GENERATION
    # ========================================================

    elif intent == "IMAGE_GENERATION":

        with st.spinner(
            "Generating your image..."
        ):

            image, error = generate_image(
                user_request
            )

        if image:

            st.session_state.generated_image = (
                image
            )

            st.session_state.generated_file = (
                None
            )

            assistant_message = (
                "I've generated the image "
                "based on your request."
            )

        else:

            assistant_message = (
                "I couldn't generate the image.\n\n"
                f"**Error:** {error}"
            )

        add_message(
            "assistant",
            assistant_message,
        )

        st.rerun()


    # ========================================================
    # IMAGE UPLOAD / VISION
    # ========================================================

    elif uploaded_images:

        vision_answers = []

        for image_data in uploaded_images:

            filename = image_data[
                "name"
            ]

            marker = (
                f"IMAGE: {filename}"
            )

            vision_result = ""

            if marker in attachment_context:

                parts = (
                    attachment_context.split(
                        marker,
                        1,
                    )
                )

                if len(parts) > 1:

                    vision_result = (
                        parts[1].strip()
                    )

            if not vision_result:

                vision_result = (
                    "The image was uploaded "
                    "successfully, but no visual "
                    "analysis was returned."
                )

            vision_answers.append(
                f"### 🖼️ {filename}\n\n"
                f"{vision_result}"
            )

        assistant_message = (
            "\n\n".join(
                vision_answers
            )
        )

        add_message(
            "assistant",
            assistant_message,
        )

        st.session_state.generated_file = (
            None
        )

        st.session_state.generated_image = (
            None
        )

        st.rerun()


    # ========================================================
    # CATALOG SEARCH
    # ========================================================

    elif intent == "CATALOG_SEARCH":

        catalog_result = search_catalog(
            user_request
        )

        if catalog_result is not None:

            if catalog_result.empty:

                assistant_message = (
                    "I couldn't find a matching "
                    "record in the available catalog."
                )

            else:

                assistant_message = (
                    "### Catalog Results\n\n"
                    + catalog_result.to_markdown(
                        index=False
                    )
                )

        else:

            assistant_message = (
                answer_library_question(
                    user_request,
                    intent,
                    attachment_context,
                )
            )

        add_message(
            "assistant",
            assistant_message,
        )

        st.session_state.generated_file = (
            None
        )

        st.session_state.generated_image = (
            None
        )

        st.rerun()


    # ========================================================
    # NORMAL QUESTION
    # ========================================================

    else:

        with st.spinner(
            "Thinking..."
        ):

            assistant_message = (
                answer_library_question(
                    user_request,
                    intent,
                    attachment_context,
                )
            )

        add_message(
            "assistant",
            assistant_message,
        )

        st.session_state.generated_file = (
            None
        )

        st.session_state.generated_image = (
            None
        )

        st.rerun()



# FOOTER


st.markdown("---")

st.caption(
    "AI Library Assistant • "
    f"Groq {GROQ_MODEL} • "
    f"Vision {GROQ_VISION_MODEL} • "
    "Cloudflare FLUX"
)
