import csv
from pathlib import Path

from mwcleric import WikiClient
from mwcleric.auth_credentials import AuthCredentials


INPUT_FILE = Path("data/classification.csv")


credentials = AuthCredentials(user_file="moths_me")

site = WikiClient(
    url="https://www2.mothphotographersgroup.msstate.edu",
    path="/w/",
    credentials=credentials
)


def add(params, name, value):
    if value is None:
        return

    value = str(value).strip()

    if value:
        params.append((name, value))


def row_to_template(row):
    params = []

    add(params, "Record ID No", row["ID"])
    add(params, "P No", row["PhylogeneticNumber"])
    add(params, "MONA MPG", row["HodgesNumber"])
    add(params, "Original Name", row["Species"])
    add(params, "Common Name", row["CommonName"])
    add(params, "Author", row["SpeciesAuthor"])

    if row["BinomialChange"].strip().lower() == "yes":
        add(params, "brackets left", "(")

    add(params, "Author Year", row["AuthorYear"])

    if row["BinomialChange"].strip().lower() == "yes":
        add(params, "brackets right", ")")

    add(params, "Parent ID No", row["Parent"])

    add(params, "Notes", row["Notes"])
    add(params, "Taxonomic Notes", row["TaxonomicNotes"])
    add(params, "Distribution", row["Distribution"])
    add(params, "Description", row["Description"])
    add(params, "Genitalia", row["Genitalia"])
    add(params, "Reference List", row["ReferenceList"])

    add(params, "Category Name", row["Level"])

    return (
        "{{ClassificationEntity\n"
        + "\n".join(f"|{name}={value}" for name, value in params)
        + "\n}}"
    )


with INPUT_FILE.open(
    newline="",
    encoding="utf-8-sig",
) as f:
    rows = list(csv.DictReader(f))


for row in rows:
    record_id = row["ID"].strip()

    if not record_id:
        print("Skipping row with no ID")
        continue

    page_title = f"Entity/{record_id}"
    page_text = row_to_template(row)

    page = site.client.pages[page_title]

    page.save(
        page_text,
        summary="Import classification data"
    )

    print(f"Saved {page_title}")
