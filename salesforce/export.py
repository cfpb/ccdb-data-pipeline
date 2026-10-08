import shutil
import tempfile

from simple_salesforce import Salesforce


def export_to_csv(query, output_file, session_id, instance):
    """Run a bulk Salesforce query and write all results to a CSV file."""
    sf = Salesforce(session_id=session_id, instance=instance)

    with tempfile.TemporaryDirectory() as tmpdir:
        results = sf.bulk2.Case.download(query, path=tmpdir, max_records=250000)

        with open(output_file, "wb") as out:
            for i, result in enumerate(results):
                with open(result["file"], "rb") as page:
                    # Skip header row on all pages except the first one.
                    if i > 0:
                        page.readline()

                    shutil.copyfileobj(page, out)
