"""Unit tests for graph domain models."""

from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    EntityType,
    GraphContext,
    Relationship,
    RelationshipType,
)


class TestEntityType:
    def test_all_variants_are_strings(self) -> None:
        for variant in EntityType:
            assert isinstance(variant.value, str)

    def test_value_equals_name_capitalized(self) -> None:
        assert EntityType.DOCUMENT.value == "Document"
        assert EntityType.PERSON.value == "Person"


class TestRelationshipType:
    def test_all_variants_are_strings(self) -> None:
        for variant in RelationshipType:
            assert isinstance(variant.value, str)


class TestEntity:
    def test_frozen(self) -> None:
        entity = Entity(
            id="e1",
            name="Volvo",
            entity_type=EntityType.ORGANIZATION,
            source_document_id="doc1",
        )
        try:
            entity.name = "changed"  # type: ignore[misc]
            assert False, "Should have raised"
        except (AttributeError, TypeError):
            pass

    def test_default_properties_empty(self) -> None:
        entity = Entity(
            id="e1",
            name="Alice",
            entity_type=EntityType.PERSON,
            source_document_id="doc1",
        )
        assert entity.properties == {}


class TestRelationship:
    def test_frozen(self) -> None:
        rel = Relationship(
            source_id="e1",
            target_id="e2",
            relationship_type=RelationshipType.MENTIONS,
        )
        try:
            rel.source_id = "changed"  # type: ignore[misc]
            assert False, "Should have raised"
        except (AttributeError, TypeError):
            pass


class TestGraphContext:
    def test_construction(self) -> None:
        entity = Entity(
            id="e1",
            name="EAC",
            entity_type=EntityType.PROJECT,
            source_document_id="doc1",
        )
        ctx = GraphContext(entity=entity, related_entities=[], relationships=[])
        assert ctx.entity.name == "EAC"
        assert ctx.related_entities == []
        assert ctx.relationships == []
