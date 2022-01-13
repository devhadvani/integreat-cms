from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..abstract_content_model import AbstractContentModel


class AbstractBasePage(AbstractContentModel):
    """
    Abstract base class for page and imprint page models.
    """

    explicitly_archived = models.BooleanField(
        default=False,
        verbose_name=_("explicitly archived"),
        help_text=_("Whether or not the page is explicitly archived"),
    )

    @property
    def archived(self):
        """
        This is an alias of ``explicitly_archived``. Used for hierarchical pages to implement a more complex notion of
        explicitly and implicitly archived pages (see :func:`~integreat_cms.cms.models.pages.page.Page.archived`).

        :return: Whether or not this page is archived
        :rtype: bool
        """
        return self.explicitly_archived

    @property
    def languages(self):
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to
        which a translation exists.

        :raises NotImplementedError: If the property is not implemented in the subclass
        """
        raise NotImplementedError

    class Meta:
        #: This model is an abstract base class
        abstract = True
