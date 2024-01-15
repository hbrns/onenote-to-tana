import argparse
import pywintypes
import win32com.client as win32
from typing import Any, Callable, Dict, Optional
from xml.etree import ElementTree

from onenote.notebooks import find_notebooks, get_notebooks, ui_handle_notebooks
from onenote.sections import find_sections, get_sections, ui_handle_sections
from onenote.pages import find_pages, handle_pages_all, ui_handle_pages


def ui_handle_elements(element_name: str, dictionary: Dict[str, ElementTree.Element], outfile: str, handler: Callable) -> bool:
    if dictionary:
        print(f'] {len(dictionary)} {element_name}')
        handler(onenote_app, dictionary, outfile)
        return True
    else:
        print(f'] no {element_name}')
        return False

def ui_handle_onenote_elements(onenote_app: Any, notebooks: Dict[str, ElementTree.Element], 
                               sections: Optional[Dict[str, ElementTree.Element]] = None, 
                               pages: Optional[Dict[str, ElementTree.Element]] = None,
                               outfile: str = None):
    if ui_handle_elements('pages', pages, outfile, ui_handle_pages): return
    if ui_handle_elements('sections', sections, outfile, ui_handle_sections): return
    if ui_handle_elements('notebooks', notebooks, outfile, ui_handle_notebooks): return

if __name__ == "__main__":
    narrowed = None
    parser = argparse.ArgumentParser(description='Convert some notes from OneNote for Tana to import.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--user', action='store_true', help='Interactively select pages for conversion')
    group.add_argument('-a', '--all', action='store_true', help='Automatically select all pages found for conversion')
    parser.add_argument('-o', '--output', type=str, metavar='FILE', help='Write to file instead of stdout')
    parser.add_argument('-n', '--notebook', type=str, help='Define the notebook (case sensitive)')
    parser.add_argument('-s', '--section', type=str, help='Define the section (case sensitive)')
    parser.add_argument('-p', '--page', nargs='+', help='Define one or multiple pages (case sensitive)')
    args = parser.parse_args()

    try:
        onenote_app = win32.gencache.EnsureDispatch("OneNote.Application.12")
        # Get the hierarchy of the notebooks, sections, and pages
        hierarchy = onenote_app.GetHierarchy("", win32.constants.hsNotebooks, "")
        # Parse the XML
        onenote_elements = ElementTree.fromstring(hierarchy)

        # first check for any arguments that narrow the search
        if args.notebook:
            pages, notebooks = find_notebooks(onenote_app, onenote_elements, args.notebook)
            if not notebooks:
                print(f'Provided notebook did not match.')
                raise KeyError
            notebooks_str = ', '.join(notebooks.keys())
            if not pages:
                print(f'{"Notebook" if len(notebooks) == 1 else "Notebooks"} "{notebooks_str}" sections have no pages. Exiting.')
                exit()
            print(f'{len(notebooks)} notebooks found: {notebooks_str}')
            narrowed = 'notebook'
        else:
            notebooks = get_notebooks(onenote_elements)

        if args.section:
            print(f'Section: {args.section}')
            pages, sections = find_sections(onenote_app, notebooks, args.section)
            if not sections:
                print(f'Provided section did not match.')
                raise KeyError
            sections_str = ', '.join(sections.keys())
            print(f'{len(sections)} section found: {sections_str}')
            narrowed = 'sections'
        else:
            sections = get_sections(onenote_app, notebooks)

        if args.page:
            pages = find_pages(onenote_app, onenote_elements, args.page)
            if not pages:
                print(f'Provided pages did not match.')
                raise KeyError
            pages_str = ', '.join(pages.keys())
            # print(f'{len(pages)} pages found: {pages_str}')
            narrowed = 'pages'

        if args.user:
            if not narrowed:    # search is not narrowed
                ui_handle_notebooks(onenote_app, notebooks, outfile=args.output)
            else:               # search is narrowed
                if 'notebook' == narrowed:
                    ui_handle_onenote_elements(onenote_app, notebooks, outfile=args.output)
                elif 'sections' == narrowed:
                    ui_handle_onenote_elements(onenote_app, notebooks, sections, outfile=args.output)
                elif 'pages' == narrowed:
                    ui_handle_onenote_elements(onenote_app, notebooks, sections, pages, outfile=args.output)
                else:
                    print(f'Somehow we ended up here. Giving up.')
                    exit()
        elif args.all:
            pages, _ = find_notebooks(onenote_app, onenote_elements, '')
            handle_pages_all(onenote_app, pages, args.output)

    except pywintypes.com_error as e:
        print(f'ERROR: {e}. Make sure the OneNote application is open.')
    except KeyError:
        print(f'Error: User selection failed. Element not found.')
