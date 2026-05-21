import re
import zipfile
import pandas as pd

# ZIP file path
zip_path = r"D:\workspace\SRH\Semester_2\NLP\WA\WhatsApp Chat - Data Science 2025 1.zip"

# Read ZIP
with zipfile.ZipFile(zip_path, "r") as zip_ref:

    txt_file = [f for f in zip_ref.namelist() if f.endswith(".txt")][0]

    with zip_ref.open(txt_file) as file:
        lines = file.read().decode("utf-8", errors="ignore").splitlines()

# WhatsApp pattern
pattern = r"^\[?(\d{1,2}\.\d{1,2}\.\d{2,4}),"

messages = []

# Extract sender + message
for line in lines:

    line = line.replace("\u200e", "").replace("\u202f", " ").strip()

    if re.match(pattern, line):

        try:
            sender = line.split("] ")[1].split(":")[0]
            message = line.split(": ", 1)[1]

            messages.append([sender, message])

        except:
            pass

# Create dataframe
df = pd.DataFrame(messages, columns=["sender", "message"])

# NLP features
df["is_question"] = df["message"].str.contains(r"\?")
df["has_link"] = df["message"].str.contains(r"http|www")

# User summary
summary = df.groupby("sender").agg(
    total_messages=("message", "count"),
    questions=("is_question", "sum"),
    links=("has_link", "sum")
).sort_values(by="total_messages", ascending=False)

# Output
print("\n===== WHATSAPP NLP ANALYSIS =====\n")

print(summary)

# Save
summary.to_excel("whatsapp_summary.xlsx")

print("\nExcel file saved: whatsapp_summary.xlsx")