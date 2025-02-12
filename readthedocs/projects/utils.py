"""Utility functions used by projects."""

import csv
import os

import structlog
from django.conf import settings
from django.http import StreamingHttpResponse

from readthedocs.core.utils.filesystem import safe_open

log = structlog.get_logger(__name__)


# TODO make this a classmethod of Version
def version_from_slug(slug, version):
    from readthedocs.api.v2.client import api
    from readthedocs.builds.models import APIVersion, Version
    if settings.DONT_HIT_DB:
        version_data = api.version().get(
            project=slug,
            slug=version,
        )['results'][0]
        v = APIVersion(**version_data)
    else:
        v = Version.objects.get(project__slug=slug, slug=version)
    return v


def safe_write(filename, contents):
    """
    Normalize and write to filename.

    Write ``contents`` to the given ``filename``. If the filename's
    directory does not exist, it is created. Contents are written as UTF-8,
    ignoring any characters that cannot be encoded as UTF-8.

    :param filename: Filename to write to
    :param contents: File contents to write to file
    """
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with safe_open(filename, "w", encoding="utf-8", errors="ignore") as fh:
        fh.write(contents)
        fh.close()


class Echo:

    """
    A class that implements just the write method of the file-like interface.

    This class can be used for generating StreamingHttpResponse.
    See: https://docs.djangoproject.com/en/2.2/howto/outputting-csv/#streaming-large-csv-files
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def get_csv_file(filename, csv_data):
    """Get a CSV file to be downloaded as an attachment."""
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in csv_data),
        content_type="text/csv",
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
