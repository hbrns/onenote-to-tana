# OneNote Sections function

import win32com.client as win32

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from typing import Any, Dict, Tuple
from xml.etree import ElementTree

from onenote.pages import get_pages, ui_handle_pages, handle_pages_all
from utilities.utils import check_substring_in_keys

def get_sections_xml(onenote_app: Any, notebook: ElementTree.Element) -> Dict[str, ElementTree.Element]:
    """
    Get the names of all sections in the selected notebook.
    """
    children = onenote_app.GetHierarchy(notebook.attrib['ID'], win32.constants.hsChildren, "")
    return {section.get('name'): section for section in ElementTree.fromstring(children) 
            if section.get('name') is not None and not section.tag.endswith('SectionGroup')}

def get_sections(onenote_app: Any, notebooks: Dict[str, ElementTree.Element]) -> Dict[str, ElementTree.Element]:
    results = {}
    for notebook in notebooks.values():
        sections = get_sections_xml(onenote_app, notebook)
        results.update(sections)
    return results

def select_section(sections: Dict[str, ElementTree.Element], section_name: str) -> Tuple[str, bool]:
    sections_str = ', '.join(sections.keys())
    print(f'Selectable sections: {sections_str}')
    all_sections = 'All' not in sections
    if all_sections:
        sections["All"] = None
    prompt_str = "To select a section type in its name or 'All' to select all: " if all_sections else "Type in the name of one section to select: "
    section_completer = WordCompleter(sections.keys(), ignore_case=True)
    selected_section = prompt(prompt_str, completer=section_completer)
    if all_sections and selected_section == "All":
        selected_section = None
    else:
        all_sections = False
    sections.pop("All", None)
    return selected_section, all_sections

def ui_handle_sections(onenote_app: Any, sections: Dict[str, ElementTree.Element], outfile: str):
    print(f'Available section: {", ".join(sections.keys())}')
    selected_section, all_sections = select_section(sections, "notebooook")
    if not all_sections:
        sections = {selected_section: sections[selected_section]}
    pages = {}
    for section in sections.values():
        section_pages = get_pages(onenote_app, section)
        pages.update(section_pages)
    if all_sections:
        handle_pages_all(onenote_app, pages, outfile)
    else:
        ui_handle_pages(onenote_app, pages, outfile)

def ui_select_section(notebook: str, sections: Dict[str, ElementTree.Element]) -> Tuple[str, bool]:
    """
    Interactively select a section from the available sections.
    """
    sections_str = ', '.join(sections.keys())
    print(f'Available section in "{notebook}" notebook: {sections_str}')
    all_sections = False
    if 'All' not in sections:
        all_sections = True
        sections["All"] = None
        prompt_str = "To select a section type in its name or 'All' to select all: "
    else:
        prompt_str = "Type in the name of one section to select: "
    section_completer = WordCompleter(sections.keys(), ignore_case=True)
    selected_section = prompt(prompt_str, completer=section_completer)
    if all_sections and selected_section == "All":
        selected_section = None
    else:
        all_sections = False
    # Remove the section with the key "All"
    sections.pop("All", None)
    return selected_section, all_sections

def handle_sections(onenote_app, notebook, notebook_name: str):
    sections = get_sections_xml(onenote_app, notebook)
    selected_section, all_sections = ui_select_section(notebook_name, sections)
    if not all_sections:
        sections = {selected_section: sections[selected_section]}
    return sections, all_sections

def find_sections(onenote_app: Any, notebooks: Dict[str, ElementTree.Element], sections_to_find: str) -> Tuple[Dict[str, ElementTree.Element], Dict[str, ElementTree.Element]]:
    results_pages = {}
    results_sections = {}
    for notebook in notebooks.values():
        sections = get_sections_xml(onenote_app, notebook)
        matches = check_substring_in_keys(sections, sections_to_find)
        if not matches:
            continue
        results_sections.update(matches)
        for section in matches.values():
            pages = get_pages(onenote_app, section)
            results_pages.update(pages)
    return results_pages, results_sections
