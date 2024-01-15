# OneNote Pages functions

import win32com.client as win32

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from typing import Any, Dict, List, Tuple
from xml.etree import ElementTree

from onenote.onenote import OneNotePageData
from utilities.utils import safe_str, extract_mht_contents

def get_pages(onenote_app: Any, section: ElementTree.Element) -> Dict[str, ElementTree.Element]:
    """
    Get the names of all pages in the selected section.
    """
    children = onenote_app.GetHierarchy(section.attrib['ID'], win32.constants.hsPages, "")
    return {page.get('name'): page for page in ElementTree.fromstring(children) if page.get('name') is not None}

def select_page(pages: Dict[str, ElementTree.Element], section_name: str) -> Tuple[str, bool]:
    pages_str = ', '.join(pages.keys())
    if section_name:
        print(f'Available pages in section "{section_name}": {pages_str}')
    else:
        print(f'Available pages in section: {pages_str}')
    all_pages = 'All' not in pages
    if all_pages:
        pages["All"] = None
    prompt_str = "To select a page type in its name or 'All' to select all: " if all_pages else "Type in the name of one page to select: "
    page_completer = WordCompleter(pages.keys(), ignore_case=True)
    selected_page = prompt(prompt_str, completer=page_completer)
    if all_pages and selected_page == "All":
        selected_page = None
    else:
        all_pages = False
    pages.pop("All", None)
    return selected_page, all_pages

def ui_handle_pages(onenote_app: Any, pages: Dict[str, ElementTree.Element], outfile: str):
    # print(f'Available pages: {", ".join(pages.keys())}')
    selected_page, all_pages = select_page(pages, None)
    if not all_pages:
        pages = {selected_page: pages[selected_page]}
    # for page in pages.values():
    #    process_page(onenote_app, page)
    handle_pages_all(onenote_app, pages, outfile)

def handle_pages(onenote_app: Any, section: ElementTree.Element, all_sections: bool):
    pages = get_pages(onenote_app, section)
    if not pages:
        print(f'Section "{section.get("name")}" has no pages. Skipping.')
        return None
    print(f'Process contents of section "{section.get("name")}".')
    if not all_sections:
        selected_page, all_pages = select_page(pages, section.get("name"))
        if not all_pages:
            pages = {selected_page: pages[selected_page]}
    return pages

def find_pages(onenote_app: Any, onenote_elements: ElementTree.Element, pages_to_find: List[str]) -> Dict:
    from onenote.notebooks import get_notebooks
    from onenote.sections import get_sections_xml
    from utilities.utils import check_substring_in_keys

    results = {}
    notebooks = get_notebooks(onenote_elements)
    for notebook_name, notebook in notebooks.items():
        sections = get_sections_xml(onenote_app, notebook)
        for section_name, section in sections.items():
            pages = get_pages(onenote_app, section)

            for substring in pages_to_find:
                matches = check_substring_in_keys(pages, substring)
                if not matches:
                    continue
                results.update(matches)
    return results

def find_page_in_notebook(onenote_app: Any, page_id: str) -> Tuple[ElementTree.Element, ElementTree.Element]:
    hierarchy_xml = onenote_app.GetHierarchy("", win32.constants.hsPages, "")
    notebooks = ElementTree.fromstring(hierarchy_xml)
    for notebook in notebooks:
        for section in notebook:
            for page in section:
                if page.get('ID') == page_id:
                    return notebook, section
    return None, None

def process_page(onenote_app: Any, directory: str, page: ElementTree.Element) -> OneNotePageData:
    import os

    # print(f'page attributes: {page.attrib}')
    page_id = page.get("ID")
    sub_page = False
    try:
        if (page.attrib['isSubPage'] == 'true'):
            sub_page = True
            print("\t", end="")
    except:
        pass
    notebook, section = find_page_in_notebook(onenote_app, page_id)

    notebook_name = notebook.get('name')
    section_name = section.get('name')
    page_name = page.get("name")

    created_at = page.get("dateTime")
    edited_at = page.get("lastModifiedTime")

    # Create a file in the directory
    file_name = f'{safe_str(page_name)}.mht'
    file_path = os.path.join(directory, file_name)

    # print(f'  > {page_name}, created at: {created_at}, edited at: {edited_at}, {notebook_name}/{section_name} {file_path}')
    print(f'> Page: "{page_name}", from "{notebook_name}" notebook section "{section_name}"')

    # Get the content of the page, as MHT
    onenote_app.Publish(page_id, file_path, win32.constants.pfMHTML, "")

    # Extract the contents of the Microsoft Hypertext Archive (MHT) file. 
    html, images = extract_mht_contents(file_path)

    page_data = OneNotePageData(
        notebook_name, 
        section_name,
        page_name,
        created_at,
        edited_at,
        sub_page,
        html,
        images
        )
    return page_data

def handle_pages_all(onenote_app: Any, pages: Dict, outfile: str) -> None:
    from onenote.convert import convert_pages_all
    convert_pages_all(onenote_app, pages, outfile)
