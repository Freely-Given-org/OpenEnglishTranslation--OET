#!/usr/bin/env python3
#
# retrieve_translation_source_texts.py
#
"""
Script to update these copies of source text files for the translation
    from their original repos (which are assumed to be already up-to-date).
"""
from gettext import gettext as _
from pathlib import Path


LAST_MODIFIED_DATE = '2022-09-01' # by RJH
SHORT_PROGRAM_NAME = "retrieveTranslationSourceTexts"
PROGRAM_NAME = "Retrieve Translation Source Texts"
PROGRAM_VERSION = '0.02'
PROGRAM_NAME_VERSION = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'
programNameVersionDate = '{} {} {}'.format( PROGRAM_NAME_VERSION, _("last modified"), LAST_MODIFIED_DATE )


DEBUGGING_THIS_MODULE = False


UHB_FOLDERPATH = Path( '/mnt/SSDs/Bibles/Original languages/UHB/' )
ULT_FOLDERPATH = Path( '/mnt/SSDs/Bibles/English translations/unfoldingWordVersions/en_ult/' )
YLT_FOLDERPATH = Path( '/mnt/SSDs/Bibles/English translations/YLT/' )
assert UHB_FOLDERPATH.is_dir()
assert ULT_FOLDERPATH.is_dir()
assert YLT_FOLDERPATH.is_dir()

project_folderpath = Path(__file__).parent.parent # Find folders relative to this module
FG_folderpath = project_folderpath.parent # Path to find parallel Freely-Given.org repos
SR_GNT_FOLDERPATH = Path( '' )
VLT_FOLDERPATH = FG_folderpath.joinpath( 'CNTR-GNT/derivedFormats/USFM/' )
assert VLT_FOLDERPATH.is_dir()


def main():
    print( f"{programNameVersionDate} started…" )
    print( "Does nothing at all yet!" )

if __name__ == '__main__':
    main()
# end of retrieve_translation_source_texts.py
