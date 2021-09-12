"""
This module contains the :class:`~cms.models.media.media_file.MediaFile` model as well as the helper functions
:func:`~cms.models.media.media_file.upload_path` and :func:`~cms.models.media.media_file.upload_path_thumbnail` which
are used to determine the file system path to which the files should be uploaded.
"""
import logging
from os.path import splitext, getmtime
from time import strftime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.formats import localize
from django.utils.translation import ugettext_lazy as _


from ...constants import allowed_media
from ..regions.region import Region
from .directory import Directory

logger = logging.getLogger(__name__)


def upload_path(instance, filename):
    """
    This function calculates the path for a file which is uploaded to the media library.
    It contains the region id, the current year and month as subdirectories and the filename.
    It is just the provisionally requested path for the media storage.
    If it already exists, Django will automatically append a random string to make sure the file name is unique.

    :param instance: The media library object
    :type instance: ~cms.models.media.media_file.MediaFile

    :param filename: The filename of media library object
    :type filename: str

    :return: The upload path of the file
    :rtype: str
    """
    # If the instance already exists in the database, make sure the upload path doesn't change
    if instance.id:
        original_instance = MediaFile.objects.get(id=instance.id)
        if original_instance.file:
            logger.debug(
                "%r already exists in the database, keeping original upload path: %r",
                instance,
                original_instance.file.name,
            )
            return original_instance.file.name

    # If the media file is uploaded to a specific region, prepend a region id subdirectory
    region_directory = f"sites/{instance.region.id}/" if instance.region else ""
    # Calculate the remaining upload path
    path = f"{region_directory}{strftime('%Y/%m')}/{filename}"
    logger.debug("Upload path for media file %r: %r", instance.file, path)
    return path


# pylint: disable=unused-argument
def upload_path_thumbnail(instance, filename):
    """
    This function derives the upload path of a thumbnail file from it's original file.
    This makes it a bit easier to determine which thumbnail belongs to which file if there are multiple files with the
    same file name (in which case Django automatically appends a random string to the original's file name).

    E.g. if the files ``A.jpg`` and ``A_thumbnail.jpg`` already exist, and ``A.jpg`` is uploaded again, the resulting
    file names might be e.g. ``A_EOHRFQ2.jpg`` and ``A_thumbnail_IWxPiOq.jpg``, while with this function, the thumbnail
    will be stored as ``A_EOHRFQ2_thumbnail.jpg``, making it easier to examine these files on the file system.

    :param instance: The media library object
    :type instance: ~cms.models.media.media_file.MediaFile

    :param filename: The (unused) initial filename of thumbnail
    :type filename: str

    :return: The upload path of the thumbnail
    :rtype: str
    """
    # If the instance already exists in the database, make sure the upload path doesn't change
    if instance.id:
        original_instance = MediaFile.objects.get(id=instance.id)
        if original_instance.thumbnail:
            logger.debug(
                "%r already exists in the database, keeping original thumbnail upload path: %r",
                instance,
                original_instance.thumbnail.name,
            )
            return original_instance.thumbnail.name

    # Derive the thumbnail name from the original file name
    name, extension = splitext(instance.file.name)
    path = f"{name}_thumbnail{extension}"
    logger.debug("Upload path for thumbnail of %r: %r", instance.thumbnail, path)
    return path


class MediaFile(models.Model):
    """
    The MediaFile model is used to store basic information about files which are uploaded to the CMS. This is only a
    virtual document and does not necessarily exist on the actual file system. Each document is tied to a region via its
    directory.
    """

    file = models.FileField(
        upload_to=upload_path,
        verbose_name=_("file"),
        max_length=512,
    )
    thumbnail = models.FileField(
        upload_to=upload_path_thumbnail,
        verbose_name=_("thumbnail file"),
        max_length=512,
    )
    type = models.CharField(
        choices=allowed_media.CHOICES,
        max_length=128,
        verbose_name=_("file type"),
    )
    name = models.CharField(max_length=512, verbose_name=_("name"))
    parent_directory = models.ForeignKey(
        Directory,
        related_name="files",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_("parent directory"),
    )
    region = models.ForeignKey(
        Region,
        related_name="files",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("region"),
    )
    alt_text = models.CharField(
        max_length=512, blank=True, verbose_name=_("description")
    )
    uploaded_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("uploaded date"),
        help_text=_("The date and time when the media file was uploaded"),
    )

    @property
    def url(self):
        """
        Returns the path of the physical file

        :return: The path of the file
        :rtype: str
        """
        return settings.BASE_URL + self.file.url if self.file else None

    @property
    def thumbnail_url(self):
        """
        Return the path of the image that should be used as the thumbnail.

        :return: The path of the file. If the file is an image and no thumbnail could be generated the file itself will be returned.
        :rtype: str
        """
        if not self.thumbnail:
            if self.type.startswith("image"):
                #: Returns the path to the file itself
                return self.url
            return None
        return settings.BASE_URL + self.thumbnail.url

    def serialize(self):
        """
        This methods creates a serialized string of that document. This can later be used in the AJAX calls.

        :return: A serialized string representation of the document for JSON concatenation
        :rtype: str
        """

        thumbnail_url = self.thumbnail_url
        if thumbnail_url:
            # Make sure replaced images are not cached
            try:
                thumbnail_url += f"?{getmtime(self.file.path)}"
            except OSError as e:
                logger.error(
                    "The physical file of %r could not be accessed: %r", self, e
                )

        return {
            "id": self.id,
            "name": self.name,
            "altText": self.alt_text,
            "type": self.type,
            "typeDisplay": self.get_type_display(),
            "thumbnailUrl": thumbnail_url,
            "url": self.url,
            "uploadedDate": localize(timezone.localtime(self.uploaded_date)),
            "isGlobal": not self.region,
        }

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``MediaFile object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the document
        :rtype: str
        """
        return self.name

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<MediaFile: MediaFile object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the document
        :rtype: str
        """
        file_path = f"path: {self.file.path}, " if self.file else ""
        return (
            f"<MediaFile (id: {self.id}, name: {self.name}, {file_path}{self.region})>"
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("media file")
        #: The plural verbose name of the model
        verbose_name_plural = _("media files")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["-region", "name"]
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The custom permissions for this model
        permissions = (
            ("upload_mediafile", "Can upload media file"),
            ("replace_mediafile", "Can replace media file"),
        )
