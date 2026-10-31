# SPDX-License-Identifier: MPL-2.0
"""2026-10-22: adapt Theographic's mixed book-code index to BOS coordinates.

Book-code conversion does not change versification. Entry contents, including
the source FGid/OSIS reference, remain intact for provenance.
"""
import logging
import bos_books_codes_py
from BibleOrgSys.Reference.BibleVersificationMappings import (
    get_default_mapping_engine, MappingStatus, VersificationMappingError)


def normalise_book_codes(index):
    """Return a BOS-keyed index, preserving metadata and rejecting collisions."""
    result, originals = {}, {}
    legacy_count = 0
    for key, entry in index.items():
        if key.startswith('__'):
            result[key] = entry
            continue
        book, separator, cv = key.partition('_')
        if not separator:
            raise ValueError(f'Theographic: invalid verse key {key!r}')
        if book == 'EZK':
            # Compatibility with loadTheographicBibleData <= 0.24, whose BOS
            # table incorrectly contained the USFM Ezekiel abbreviation.
            book = bos_books_codes_py.usfm_abbrev_to_bos_book_code(book)
            legacy_count += 1
        elif not bos_books_codes_py.is_valid_bos_book_code(book):
            raise ValueError(f'Theographic: expected a BOS book code in {key!r}; '
                             'regenerate the index with loadTheographicBibleData.py')
        normalised = f'{book}_{cv}'
        if normalised in result:
            raise ValueError(f'Theographic: {originals[normalised]!r} and {key!r} '
                             f'both resolve to BOS reference {normalised!r}')
        result[normalised] = entry
        originals[normalised] = key
    if legacy_count:
        logging.warning('Theographic: corrected %s legacy EZK keys to BOS EZE; regenerate '
                        'the data with the updated Bible_speaker_identification/Scripts/'
                        'loadTheographicBibleData.py', legacy_count)
    return result


def mapped_verse_metadata(verseRef, verseIndex, source_profile, *, dataset='Theographic JSON'):
    """Combine metadata for the complete BOS passage corresponding to a native verse.

    These are verse-level annotations, so an indivisible target verse supplies
    metadata to each of its source parts. BOS alone determines those groups.
    Keep all distinct annotations, including different years/timelines, without
    changing the word-table reference, word numbers, row order, or glosses.
    Missing mappings/data stop the build before write_new_table can save an
    incompletely tagged table; they never fall back to a same-number JSON key.
    """
    BBB, CV = verseRef.split('_')
    C, V = CV.split(':')
    mapping = get_default_mapping_engine().convert_passage(
        source_profile, 'KJV', ((BBB,C,V,None),))
    if mapping.status != MappingStatus.EXACT:
        raise ValueError(f'Cannot tag {source_profile} word-table verse {verseRef} '
            f'from KJV Theographic data: {mapping.status.value}; '
            + '; '.join(d.message for d in mapping.diagnostics)) from VersificationMappingError(mapping)
    metadata = {field:[] for field in ('people','peopleGroups','places','eventsDescribed','yearNums','timelines')}
    for book,chapter,verse,suffix in mapping.references:
        key = f'{book}_{chapter}:{verse}{suffix or ""}'
        try:
            entry = verseIndex[key]
        except KeyError as error:
            # Theographic has no records for unnumbered Psalm titles. BOS must
            # explicitly map to zero; missing numbered records are still errors.
            if book == 'PSA' and verse == '0' and not suffix:
                continue
            raise ValueError(f'Cannot tag {source_profile} word-table verse {verseRef}: '
                f'mapped KJV key {key} is missing from '
                f'Theographic data {dataset}') from error
        for field,outputField in (('people','people'), ('peopleGroups','peopleGroups'),
                ('places','places'), ('eventsDescribed','eventsDescribed'),
                ('yearNum','yearNums'), ('timeline','timelines')):
            value = entry[field]
            scalar = field in ('yearNum','timeline')
            if not isinstance(value, str if scalar else list):
                raise ValueError(f'Invalid Theographic {key} field {field}: {value!r}')
            for annotation in ([value] if scalar else value):
                if annotation and annotation not in metadata[outputField]:
                    metadata[outputField].append(annotation)
    return metadata
