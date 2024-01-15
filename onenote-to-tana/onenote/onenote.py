from typing import Dict

class OneNotePageData():
    def __init__(self, nodebookName: str, sectionName: str, pageName: str, createdAt: str, editedAt: str, isSubPage: bool, html_string: str, images: Dict[str, str]):
        self.nodebookName = nodebookName
        self.sectionName = sectionName
        self.pageName = pageName
        self.createdAt = createdAt
        self.editedAt = editedAt
        self.isSubPage = isSubPage
        self.html_string = html_string
        self.images = images
