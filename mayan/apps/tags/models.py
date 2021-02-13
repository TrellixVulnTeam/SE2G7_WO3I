from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from colorful.fields import RGBColorField

from mayan.apps.acls.models import AccessControlList
from mayan.apps.common.model_mixins import ExtraDataModelMixin
from mayan.apps.events.classes import EventManagerSave
from mayan.apps.events.decorators import method_event
from mayan.apps.documents.models import Document
from mayan.apps.documents.permissions import permission_document_view

from .events import (
    event_tag_attached, event_tag_created, event_tag_edited, event_tag_removed
)
from .html_widgets import widget_single_tag


class Tag(ExtraDataModelMixin, models.Model):
    """
    This model represents a binary property that can be applied to a document.
    The tag can have a label and a color.
    """
    label = models.CharField(
        db_index=True, help_text=_(
            'A short text used as the tag name.'
        ), max_length=128, unique=True, verbose_name=_('Label')
    )
    color = RGBColorField(
        help_text=_('The RGB color values for the tag.'),
        verbose_name=_('Color')
    )
    documents = models.ManyToManyField(
        related_name='tags', to=Document, verbose_name=_('Documents')
    )

    class Meta:
        ordering = ('label',)
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    def __str__(self):
        return self.label

    def attach_to(self, document, user=None):
        """
        Attach a tag to a document and commit the corresponding event.
        """
        self.documents.add(document)
        event_tag_attached.commit(
            action_object=self, actor=user, target=document
        )

    def get_absolute_url(self):
        return reverse(
            viewname='tags:tag_document_list', kwargs={'tag_id': self.pk}
        )

    def get_document_count(self, user):
        """
        Return the numeric count of documents that have this tag attached.
        The count is filtered by access.
        """
        queryset = AccessControlList.objects.restrict_queryset(
            permission=permission_document_view, queryset=self.documents,
            user=user
        )

        return queryset.count()

    def get_documents(self, user):
        """
        Return a filtered queryset documents that have this tag attached.
        """
        return AccessControlList.objects.restrict_queryset(
            permission=permission_document_view, queryset=self.documents.all(),
            user=user
        )

    def get_preview_widget(self):
        return widget_single_tag(tag=self)
    get_preview_widget.short_description = _('Preview')

    def remove_from(self, document, user=None):
        """
        Remove a tag from a document and commit the corresponding event.
        """
        self.documents.remove(document)
        event_tag_removed.commit(
            action_object=self, actor=user, target=document
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_tag_created,
            'target': 'self',
        },
        edited={
            'event': event_tag_edited,
            'target': 'self',
        }
    )
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class DocumentTag(Tag):
    class Meta:
        proxy = True
        verbose_name = _('Document tag')
        verbose_name_plural = _('Document tags')
