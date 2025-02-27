# DOCUMENT PROCESSING

# ---------------------------------------------------------------------------
# IMPORT LIBRARIES

import datetime
from typing import Optional

from sqlalchemy import or_

from database.models import Documents, Data
from logger import print_error, logger


# ---------------------------------------------------------------------------
# DOCUMENT PROCESSING

def find_non_processed_document(document_type: Optional[str] = 'transfer_document') -> Optional["Documents"]:
    """
       Retrieve the earliest non-processed document from the database.

       Args:
           document_type (Optional[str]): The type of document to filter by. Defaults to 'transfer_document'.

       Returns:
           Optional[Documents]: The first document that matches the criteria, or None if no document is found.
    """

    query = Documents.filter(Documents.processed_at == None)
    if document_type:
        query = query.filter(Documents.document_type == document_type)

    query = query.order_by(Documents.recieved_at.asc())
    return query.first()


def process_document_objects(document: Documents) -> bool:
    """
    Processes data objects linked to the given document.

    Validates the document's data, updates matching Data objects per operation details,
    marks the document as processed, and returns the processing status.

    Args:
        document (Documents): The document to process.

    Returns:
        bool: True if processing is successful, otherwise False.
    """

    try:
        logger.debug(f"{document.doc_id} -- Начинаем обработку")

        if document.document_data.get('document_data').get('document_id') != document.doc_id:
            logger.debug(f"{document.doc_id} -- несоответствие данных операции - document_id")
            return False

        if document.document_data.get('document_data').get('document_type') != document.document_type:
            logger.debug(f"{document.doc_id} -- несоответствие данных операции - document_type")
            return False

        object_keys = document.document_data.get('objects', [])
        for key, change_data in document.document_data.get('operation_details', {}).items():
            # Retrieves Data records matching the specified object_keys and old values for update
            filter_condition = or_(
                Data.object.in_(object_keys),
                Data.parent.in_(object_keys)
            ) & (getattr(Data, key) == change_data.get('old'))

            updated_count = Data.update_all(filter_condition, {key: change_data.get('new')})
            logger.debug(f"Обновлено {updated_count} записей для поля {key}: "
                         f"{change_data.get('old')} -> {change_data.get('new')}")

        document.processed_at = datetime.datetime.now()
        document.save()
        logger.debug(f"{document.doc_id} -- Обработан")
        return True

    except Exception as e:
        logger.debug(f"{document.doc_id} -- Возникла ошибка при обработке")
        print_error(e)

    return False


def process_document() -> bool:
    """
    Main function to process a single document.

    This function retrieves a non-processed document and processes its associated objects.
    If there is no document to process or an error occurs, it returns False.

    Returns:
        bool: True if a document was processed successfully; False otherwise.
    """

    try:
        document = find_non_processed_document()
        if not document:
            return False

        return process_document_objects(document)

    except Exception as error:
        print_error(error)
    return False


if __name__ == '__main__':
    process_document_result = process_document()
    print(f'Результат обработки документа: {process_document_result}')
