# OneNote Notebooks functions

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from typing import Any, Dict, Optional, Tuple
from xml.etree import ElementTree

from onenote.sections import get_sections_xml, ui_handle_sections
from onenote.pages import get_pages, handle_pages_all
from utilities.utils import check_substring_in_keys

def ui_select_notebook(notebooks: Dict[str, ElementTree.Element], all: Optional[bool] = False) -> str:
    """
    Interactively select a notebook from the available notebooks.
    """
    print("Available notebooks:", ', '.join(notebooks.keys()))
    all_notebooks = False
    if all:
        # check for a notebook called 'All' (not)
        all_notebooks = 'All' not in notebooks
        if all_notebooks:
            notebooks["All"] = None
    notebook_completer = WordCompleter(notebooks.keys(), ignore_case=True)
    prompt_str = "To select a notebook type in its name or 'All' to select all: " if all_notebooks else "Select one notebook by typing in its name: "
    selected_notebook = prompt(prompt_str, completer=notebook_completer)
    if all_notebooks and selected_notebook == "All":
        selected_notebook = None
    else:
        all_notebooks = False
    notebooks.pop("All", None)
    return selected_notebook, all_notebooks

def ui_handle_notebooks(onenote_app: Any, notebooks: Dict[str, ElementTree.Element], outfile: str):
    selected_notebook, all_notebooks = ui_select_notebook(notebooks, True)
    if not all_notebooks:
        notebooks = {selected_notebook: notebooks[selected_notebook]}
    sections = {}
    for notebook in notebooks.values():
        notebook_sections = get_sections_xml(onenote_app, notebook)
        sections.update(notebook_sections)

    if all_notebooks:
        pages = {}
        for section in sections.values():
            section_pages = get_pages(onenote_app, section)
            pages.update(section_pages)
        handle_pages_all(onenote_app, pages, outfile)
    else:
        ui_handle_sections(onenote_app, sections, outfile)

def find_notebooks(onenote_app: Any, onenote_elements: ElementTree.Element, notebooks_to_find: str) -> Tuple[Dict, Dict]:
    notebooks = get_notebooks(onenote_elements)
    if str:
        matches = check_substring_in_keys(notebooks, notebooks_to_find)
        if 0 == len(matches):
            raise KeyError
    else:
        matches = notebooks.copy()

    results = {}
    for notebook in matches.values():
        sections = get_sections_xml(onenote_app, notebook)
        for section in sections.values():
            pages = get_pages(onenote_app, section)
            results.update(pages)
    return results, matches

def get_notebooks(elements: ElementTree.Element) -> Dict[str, ElementTree.Element]:
    """
    Create a dictionary to map notebook names to their XML elements.
    """
    return {notebook.get('name') if notebook.get('name') is not None else "None": notebook for notebook in elements}
