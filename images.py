import csv
from pathlib import Path

import mwclient
from mwcleric import WikiClient
from mwcleric.auth_credentials import AuthCredentials


CSV_FILE = "data/images.csv"
IMAGE_DIR = Path("data/images")


credentials = AuthCredentials(user_file="moths_me")

site = WikiClient(
    url="https://www2.mothphotographersgroup.msstate.edu",
    path="/w/",
    credentials=credentials,
)


def yes(value):
    return str(value).strip() == "1"


def add(params, name, value):
    if value is None:
        return

    value = str(value).strip()

    if value:
        params.append((name, value))


def make_wikitext(row):
    params = []

    add(params, "Hodges Number", row["HodgesNumber"])
    add(params, "Coordinates", row["Coordinates"])
    add(params, "Live Collection", row["LiveCollection"])
    add(params, "Credit", row["Credit"])

    add(
        params,
        "IsGenitalia",
        "Yes" if yes(row["IsGenitalia"]) else "No",
    )

    add(params, "Reviewed", "Yes")
    add(params, "Approved", "Yes")

    lines = ["{{Image Upload"]

    for name, value in params:
        lines.append(f"|{name}={value}")

    lines.append("}}")

    return "\n".join(lines)


def upload_image(row):
    relative_path = Path(row["FilePath"])
    local_path = IMAGE_DIR / relative_path

    if not local_path.exists():
        print(f"NOT FOUND: {local_path}")
        return

    filename = relative_path.name
    page_title = f"File:{filename}"
    wikitext = make_wikitext(row)

    print(f"Uploading {local_path} -> {page_title}")

    try:
        with open(local_path, "rb") as f:
            site.client.upload(
                f,
                filename=filename,
                description=wikitext,
                ignore=True,
            )

        print(f"Uploaded {page_title}")

    except mwclient.errors.APIError as e:
        if e.code in ("fileexists-no-change", "fileexists-shared-forbidden"):
            print(f"{page_title} already exists; updating description page")

            page = site.client.pages[page_title]
            page.save(
                wikitext,
                summary="Updating image metadata",
            )

            print(f"Updated {page_title}")

        else:
            raise


with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        try:
            upload_image(row)
        except Exception as e:
            print(f"ERROR uploading {row['FilePath']}: {e}")
