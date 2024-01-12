from typing import List, Optional, TypeVar
from enum import Enum

# NodeType = 'field' | 'image' | 'codeblock' | 'node' | 'date'
class NodeType(Enum):
    FIELD = 'field'
    IMAGE = 'image'
    CODEBLOCK = 'codeblock'
    NODE = 'node'
    DATE = 'date'

    def to_dict(self):
        return self.value

# DataType = 'any' | 'url' | 'email' | 'number' | 'date' | 'checkbox'
class DataType(Enum):
    ANY = 'any'
    URL = 'url'
    EMAIL = 'email'
    NUMBER = 'number'
    DATE = 'date'
    CHECKBOX = 'checkbox'

    def to_dict(self):
        return self.value

class Tana:
    def to_dict(self):
        return self.__dict__

class TanaIntermediateSummary(Tana):
    def __init__(self, leafNodes: int, topLevelNodes: int, totalNodes: int, calendarNodes: int, fields: int, brokenRefs: int):
        self.leafNodes = leafNodes
        self.topLevelNodes = topLevelNodes
        self.totalNodes = totalNodes
        self.calendarNodes = calendarNodes
        self.fields = fields
        self.brokenRefs = brokenRefs

class TanaIntermediateAttribute(Tana):
    def __init__(self, name: str, values: List[str], count: int, dataType: Optional[DataType] = None):
        self.name = name
        self.values = values
        self.count = count
        self.dataType = dataType

class TanaIntermediateSupertag(Tana):
    def __init__(self, uid: str, name: str):
        self.uid = uid
        self.name = name

T = TypeVar('T', bound='TanaIntermediateNode')

class TanaIntermediateNode(Tana):
    def __init__(self, uid: str, name: str, description: Optional[str] = None, children: Optional[List[T]] = None, refs: Optional[List[str]] = None, createdAt: int = -1, editedAt: int = -1, type: str = '', mediaUrl: Optional[str] = None, codeLanguage: Optional[str] = None, supertags: Optional[List[str]] = None, todoState: Optional[str] = None):
        self.uid = uid
        self.name = name
        self.description = description
        self.children = children
        self.refs = refs
        self.createdAt = createdAt
        self.editedAt = editedAt
        self.type = type
        self.mediaUrl = mediaUrl
        self.codeLanguage = codeLanguage
        self.supertags = supertags
        self.todoState = todoState

    def to_dict(self):
        return {
            **self.__dict__,
            'type': self.type.value if isinstance(self.type, NodeType) else self.type,
            'children': [child.to_dict() if isinstance(child, TanaIntermediateNode) else child for child in self.children] if self.children else []
        }

class TanaIntermediateFile(Tana):
    def __init__(self, summary: TanaIntermediateSummary, nodes: List[TanaIntermediateNode], attributes: Optional[List[TanaIntermediateAttribute]] = None, supertags: Optional[List[TanaIntermediateSupertag]] = None):
        self.version = 'TanaIntermediateFile V0.1'
        self.summary = summary
        self.nodes = nodes
        self.attributes = attributes
        self.supertags = supertags

    def to_dict(self):
        try:
            return {
                'version': self.version,
                'summary': self.summary.to_dict(),
                'nodes': [node.to_dict() for node in self.nodes],
                'attributes': [attribute.to_dict() if isinstance(attribute, TanaIntermediateAttribute) else attribute for attribute in self.attributes] if self.attributes else [],
                'supertags': [supertag.to_dict() if isinstance(supertag, TanaIntermediateSupertag) else supertag for supertag in self.supertags] if self.supertags else [],
            }
        except AttributeError as e:
            print(f"Error: {e}")
            print(f"self.nodes: {self.nodes}")
            print(f"self.attributes: {self.attributes}")
            print(f"self.supertags: {self.supertags}")
