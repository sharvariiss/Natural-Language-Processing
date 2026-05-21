import re
import zipfile
import pandas as pd
from collections import Counter
from urllib.parse import urlparse

# -----------------------------
# 1. Load WhatsApp Export ZIP
# -----------------------------

zip_path = r"D:\workspace\SRH\Semester_2\NLP\WA\WhatsApp Chat - Data Science 2025 1.zip"

with zipfile.ZipFile(zip_path, "r") as zip_ref:

    # Get all files inside ZIP
    file_names = zip_ref.namelist()

    print("\nFiles found inside ZIP:\n")

    for f in file_names:
        print(f)

    # Find txt file safely
    txt_files = [f for f in file_names if f.lower().endswith(".txt")]

    if len(txt_files) == 0:
        raise Exception("No TXT chat file found inside ZIP!")

    # Use first txt file
    chat_file = txt_files[0]

    print(f"\nUsing chat file: {chat_file}")

    # Read chat file
    with zip_ref.open(chat_file) as file:
        lines = file.read().decode("utf-8", errors="ignore").splitlines()


# # -----------------------------
# # 2. Parse WhatsApp Messages
# # -----------------------------

# pattern = r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s([^:]+):\s(.*)"

# messages = []

# for line in lines:

#     match = re.match(pattern, line)

#     if match:
#         date, time, sender, message = match.groups()

#         messages.append({
#             "date": date,
#             "time": time,
#             "sender": sender.strip(),
#             "message": message.strip()
#         })

#     else:
#         # Multi-line messages
#         if messages:
#             messages[-1]["message"] += " " + line.strip()

# df = pd.DataFrame(messages)

# print(f"\nTotal messages parsed: {len(df)}")


# # -----------------------------
# # 3. Text Cleaning
# # -----------------------------

# def clean_text(text):

#     text = text.lower()

#     # Replace links
#     text = re.sub(r"http\S+|www\S+", " LINK ", text)

#     # Remove emojis/symbols
#     text = re.sub(r"[^a-zA-Z0-9\s?]", " ", text)

#     # Remove extra spaces
#     text = re.sub(r"\s+", " ", text).strip()

#     return text


# df["clean_message"] = df["message"].apply(clean_text)

# -----------------------------
# 2. Parse WhatsApp Messages
# -----------------------------

patterns = [
    # Android format: 18/05/2026, 10:30 - Name: Message
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s([^:]+):\s(.*)",

    # iPhone format: [18/05/2026, 10:30:12] Name: Message
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}(?::\d{2})?)\]\s([^:]+):\s(.*)",

    # iPhone format with dash: [18/05/2026, 10:30:12] - Name: Message
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}(?::\d{2})?)\]\s-\s([^:]+):\s(.*)"
]

messages = []

for line in lines:
    matched = False

    for pattern in patterns:
        match = re.match(pattern, line)

        if match:
            date, time, sender, message = match.groups()

            messages.append({
                "date": date,
                "time": time,
                "sender": sender.strip(),
                "message": message.strip()
            })

            matched = True
            break

    if not matched:
        if messages:
            messages[-1]["message"] += " " + line.strip()

df = pd.DataFrame(messages)

print("\nTotal messages parsed:", len(df))
print("Columns:", df.columns.tolist())

if df.empty:
    print("\nNo messages parsed. First 20 lines from chat file:")
    for line in lines[:20]:
        print(line)
    raise Exception("Parser could not detect your WhatsApp format.")


# -----------------------------
# 4. NLP Feature Extraction
# -----------------------------

def count_links(text):
    return len(re.findall(r"http\S+|www\S+", text))


def is_question(text):

    question_words = [
        "what", "why", "when", "where",
        "who", "how", "which", "can",
        "could", "do", "does", "is", "are"
    ]

    text_lower = text.lower()

    return (
        "?" in text
        or any(text_lower.startswith(word + " ") for word in question_words)
    )


def word_count(text):
    return len(text.split())


def char_count(text):
    return len(text)


def contains_media(text):

    media_patterns = [
        "<media omitted>",
        "image omitted",
        "video omitted",
        "audio omitted",
        "sticker omitted",
        "document omitted"
    ]

    return any(pattern in text.lower() for pattern in media_patterns)


df["word_count"] = df["clean_message"].apply(word_count)

df["char_count"] = df["message"].apply(char_count)

df["link_count"] = df["message"].apply(count_links)

df["is_question"] = df["message"].apply(is_question)

df["has_media"] = df["message"].apply(contains_media)


# -----------------------------
# 5. User-wise Analysis
# -----------------------------

summary = df.groupby("sender").agg(
    total_messages=("message", "count"),
    total_words=("word_count", "sum"),
    total_characters=("char_count", "sum"),
    questions_asked=("is_question", "sum"),
    links_sent=("link_count", "sum"),
    media_sent=("has_media", "sum")
).reset_index()

summary["avg_words_per_message"] = (
    summary["total_words"] / summary["total_messages"]
).round(2)

summary = summary.sort_values(
    by="total_messages",
    ascending=False
)


# -----------------------------
# 6. Link Domain Analysis
# -----------------------------

def extract_domains(text):

    urls = re.findall(r"http\S+|www\S+", text)

    domains = []

    for url in urls:

        if not url.startswith("http"):
            url = "https://" + url

        try:
            domain = urlparse(url).netloc
            domains.append(domain)

        except:
            pass

    return domains


all_domains = []

for msg in df["message"]:
    all_domains.extend(extract_domains(msg))


domain_summary = pd.DataFrame(
    Counter(all_domains).items(),
    columns=["domain", "count"]
)

domain_summary = domain_summary.sort_values(
    by="count",
    ascending=False
)


# -----------------------------
# 7. Export Results
# -----------------------------

output_file = "whatsapp_nlp_classification.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:

    df.to_excel(
        writer,
        sheet_name="Parsed Messages",
        index=False
    )

    summary.to_excel(
        writer,
        sheet_name="User Summary",
        index=False
    )

    domain_summary.to_excel(
        writer,
        sheet_name="Link Domains",
        index=False
    )

print("\nAnalysis completed successfully!")

print(f"\nOutput saved as: {output_file}")


# -----------------------------
# 8. Quick Console Insights
# -----------------------------

print("\nTop 5 users by messages:\n")

print(
    summary[
        ["sender", "total_messages"]
    ].head()
)

print("\nTop 5 users by questions:\n")

print(
    summary[
        ["sender", "questions_asked"]
    ].sort_values(
        by="questions_asked",
        ascending=False
    ).head()
)

print("\nTop 5 users by links:\n")

print(
    summary[
        ["sender", "links_sent"]
    ].sort_values(
        by="links_sent",
        ascending=False
    ).head()
)