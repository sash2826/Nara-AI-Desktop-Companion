"""Shared domain models for the knowledge graph capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EntityType(str, Enum):
    DOCUMENT = "Document"
    PERSON = "Person"
    ORGANIZATION = "Organization"
    PROJECT = "Project"
    TECHNOLOGY = "Technology"
    CONCEPT = "Concept"
    LOCATION = "Location"
    EVENT = "Event"


class RelationshipType(str, Enum):
    MENTIONS = "MENTIONS"
    RELATED_TO = "RELATED_TO"
    BELONGS_TO = "BELONGS_TO"
    REFERENCES = "REFERENCES"
    AUTHORED_BY = "AUTHORED_BY"
    PART_OF = "PART_OF"


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    entity_type: EntityType
    source_document_id: str
    properties: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Relationship:
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GraphContext:
    """Context retrieved from the knowledge graph for a given query entity."""
    entity: Entity
    related_entities: list[Entity]
    relationships: list[Relationship]
