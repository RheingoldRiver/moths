import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from mwcleric import WikiClient
from mwcleric.auth_credentials import AuthCredentials


INPUT_FILE = Path("data/classification.csv")
MAPPING_FILE = Path("data/mapping.csv")


credentials = AuthCredentials(user_file="moths_me")

site = WikiClient(
    url="https://www2.mothphotographersgroup.msstate.edu",
    path="/w/",
    credentials=credentials,
)


def add(params, name, value):
    """
    Add a template parameter only if it has a non-empty value.
    """
    if value is None:
        return

    value = str(value).strip()

    if value:
        params.append((name, value))


def numeric_hodges(value):
    value = str(value).strip()

    if not value:
        return None

    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def mapping_to_template(row):
    fields = [
        ("source", "source"),
        ("type", "type"),
        # ("species", "species"),
        ("state", "state"),
        ("county", "county"),
        ("lati", "lat"),
        ("long", "lon"),
        ("date", "date"),
    ]

    parts = ["{{Observation"]

    for csv_name, template_name in fields:
        parts.append(f"|{template_name}={row[csv_name].strip()}")

    parts.append("}}")

    return "".join(parts)

def references(txt):
    # Entries are separated by ";;;". A single ";" is ordinary text, including
    # the end of entities like &amp;, so splitting on it breaks references apart.
    return "".join(
        f"{{{{Reference|ref={item.strip()}}}}}"
        for item in txt.split(";;;")
        if item.strip()
    )


def row_to_template(row):
    params = []

    add(params, "Record ID No", row["ID"])
    add(params, "P No", row["PhylogeneticNumber"])
    add(params, "MONA MPG", row["HodgesNumber"])
    add(params, "Original Name", row["Species"])
    add(params, "Common Name", row["CommonName"])
    add(params, "Author", row["SpeciesAuthor"])
    add(params, "Binomial Change", row["BinomialChange"])

    add(params, "Author Year", row["AuthorYear"])

    add(params, "Parent ID No", row["Parent"])

    # Template:ClassificationEntity stores SynonymOf, PhylogeneticRevision and
    # LevelNumber from these names. Its Synonymy parameter is the synonymy list
    # shown on species pages, not this ID.
    add(params, "synonymID", row["SynonymOf"])
    add(params, "P Revision", row["PhylogeneticRevision"])
    add(params, "Category No", row["LevelNumber"])

    add(params, "Notes", row["Notes"])
    add(params, "Taxonomic Notes", row["TaxonomicNotes"])
    add(params, "Distribution", row["Distribution"])
    add(params, "Description", row["Description"])
    add(params, "Genitalia", row["Genitalia"])
    add(params, "Reference List", references(row["ReferenceList"]))

    hodges = numeric_hodges(row["HodgesNumber"])

    if hodges is not None and hodges in mappings_by_hodges:
        mapping_text = "".join(
            mapping_to_template(mapping_row)
            for mapping_row in mappings_by_hodges[hodges]
        )
        add(params, "mapping", mapping_text)

    add(params, "Category Name", row["Level"])

    return (
        "{{ClassificationEntity\n"
        + "\n".join(f"|{name}={value}" for name, value in params)
        + "\n}}"
    )


# Load mapping.csv into memory, indexed by numeric Hodges number.
mappings_by_hodges = defaultdict(list)

with MAPPING_FILE.open(
    newline="",
    encoding="utf-8-sig",
) as f:
    for row in csv.DictReader(f):
        hodges = numeric_hodges(row["hodges"])

        if hodges is not None:
            mappings_by_hodges[hodges].append(row)


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
        summary="Update from new data"
    )

    print(f"Saved {page_title}")
