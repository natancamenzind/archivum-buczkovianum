"""Staff-only fragment API for the tagger (architecture section 7)."""

from typing import Any

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from archive.models import Document, Fragment, Tag
from archive.tagger import tagger_fragments


class EditorTagSerializer(serializers.ModelSerializer[Tag]):
    class Meta:
        model = Tag
        fields = ("id", "title")
        read_only_fields = fields


class EditorFragmentSerializer(serializers.ModelSerializer[Fragment]):
    start = serializers.IntegerField(min_value=0)
    end = serializers.IntegerField(min_value=0)
    quote = serializers.CharField()
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        source="tags",
        write_only=True,
        allow_empty=False,
    )
    tags = EditorTagSerializer(many=True, read_only=True)

    class Meta:
        model = Fragment
        fields = (
            "id",
            "document",
            "start",
            "end",
            "quote",
            "tag_ids",
            "tags",
            "needs_review",
        )
        read_only_fields = ("id", "needs_review")

    def get_fields(self) -> dict[str, serializers.Field[Any, Any, Any, Any]]:
        fields = super().get_fields()
        if self.instance is not None:
            for name in ("document", "start", "end", "quote"):
                fields[name].read_only = True
        return fields

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        document = attrs.get("document") or getattr(self.instance, "document", None)
        if document is None:
            return attrs
        if not document.offers_tagger():
            raise serializers.ValidationError({"document": "This text cannot be tagged."})
        start = attrs.get("start", getattr(self.instance, "start", None))
        end = attrs.get("end", getattr(self.instance, "end", None))
        quote = attrs.get("quote")
        if start is not None and end is not None and quote is not None:
            text_len = len(document.text)
            if start < 0 or end < 0 or start >= end or end > text_len:
                raise serializers.ValidationError(
                    {"end": "The selection must lie within the document text."}
                )
            if document.text[start:end] != quote:
                raise serializers.ValidationError(
                    {"quote": "The quote must match the selected text."}
                )
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Fragment:
        tags = validated_data.pop("tags")
        with transaction.atomic():
            fragment = Fragment.objects.create(**validated_data)
            self._save_tags(fragment, tags)
        return fragment

    def update(self, instance: Fragment, validated_data: dict[str, Any]) -> Fragment:
        tags = validated_data.pop("tags", None)
        if tags is not None:
            with transaction.atomic():
                self._save_tags(instance, tags)
        return instance

    def _save_tags(self, fragment: Fragment, tags: list[Tag]) -> None:
        fragment.tags.set(tags)
        fragment.update_search_entry()
        Tag.update_search_entries()


class EditorFragmentListCreate(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(responses=EditorFragmentSerializer(many=True))
    def get(self, request: Request) -> Response:
        document_id = request.query_params.get("document")
        if not document_id:
            return Response(
                {"document": "This query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        document = Document.objects.filter(pk=document_id).first()
        if document is None or not document.offers_tagger():
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(EditorFragmentSerializer(tagger_fragments(document), many=True).data)

    @extend_schema(request=EditorFragmentSerializer, responses=EditorFragmentSerializer)
    def post(self, request: Request) -> Response:
        serializer = EditorFragmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fragment = serializer.save()
        return Response(
            EditorFragmentSerializer(fragment).data,
            status=status.HTTP_201_CREATED,
        )


class EditorFragmentDetail(APIView):
    permission_classes = (IsAdminUser,)

    def _fragment(self, pk: int) -> Fragment | None:
        fragment = (
            Fragment.objects.select_related(
                *[f"document__{owner}" for owner in Document.owner_accessors()]
            )
            .filter(pk=pk)
            .first()
        )
        if fragment is None or not fragment.document.offers_tagger():
            return None
        return fragment

    @extend_schema(request=EditorFragmentSerializer, responses=EditorFragmentSerializer)
    def patch(self, request: Request, pk: int) -> Response:
        fragment = self._fragment(pk)
        if fragment is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = EditorFragmentSerializer(fragment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        fragment = serializer.save()
        return Response(EditorFragmentSerializer(fragment).data)

    @extend_schema(responses={204: None})
    def delete(self, request: Request, pk: int) -> Response:
        fragment = self._fragment(pk)
        if fragment is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        fragment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
