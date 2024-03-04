from datetime import datetime
from datetime import timezone
from typing import Any

from .hermes import Hermes  # type: ignore

from danswer.configs.app_configs import INDEX_BATCH_SIZE
from danswer.configs.constants import DocumentSource
from danswer.connectors.interfaces import GenerateDocumentsOutput
from danswer.connectors.interfaces import LoadConnector
from danswer.connectors.interfaces import PollConnector
from danswer.connectors.interfaces import SecondsSinceUnixEpoch
from danswer.connectors.models import ConnectorMissingCredentialError
from danswer.connectors.models import Document
from danswer.connectors.models import Section
from danswer.utils.logger import setup_logger

HERMES_URL = "https://hermesapp.net/api/"

logger = setup_logger()

class HermesConnector(LoadConnector, PollConnector):
    def __init__(
        self, batch_size: int = INDEX_BATCH_SIZE, access_token: str | None = None
    ) -> None:
        self.batch_size = batch_size//2
        self.access_token = access_token
        self.portal_id: str | None = None
        self.base_url = HERMES_URL


    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        self.access_token = credentials["hermes_access_token"]

        return None

    def _process_messages(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> GenerateDocumentsOutput:
        """
        Retrieves Messages and Makes them Searchable
        """
        if self.access_token is None:
            raise ConnectorMissingCredentialError("Hermes")
        
        api_client = Hermes(access_token=self.access_token)
        message_threads = api_client.get_all_message_threads()

        doc_batch: list[Document] = []

        for thread in message_threads:
            updated_at = datetime.fromisoformat(
                thread.get("last_updated")
            )
            if start is not None and updated_at is not None and updated_at < start:
                continue
            if end is not None and updated_at is not None and updated_at > end:
                continue
                
            messages = thread.get("messages")

            link = f"{HERMES_URL}threads/{thread.get('_id')}"

            message_texts = []

            for message in messages:
                context = f"From: {message.get('sender_username')}\n \
                            Filename: {message.get('filename')}\n \
                            Code: {message.get('snippet')}\n \
                            Message: {message.get('message')}"
                message_texts.append(context)

            message_text = '\n'.join(message_texts)
            context_text = f"Messages: {message_text}"

            doc_batch.append(
                Document(
                    id=thread.get("_id"),
                    sections=[Section(link=link, text=context_text)],
                    source=DocumentSource.HERMES, 
                    semantic_identifier=thread.get("_id"),
                    doc_updated_at=datetime.fromisoformat(
                        str(updated_at)
                    ).astimezone(timezone.utc),
                    metadata={
                        "enterprise_id": thread.get("enterprise_id"),
                        "type":"message"
                    }
                )
            )

            if len(doc_batch) >= self.batch_size:
                yield doc_batch
                doc_batch = []
        
        if doc_batch:
            yield doc_batch


    def _process_spaces(self) -> GenerateDocumentsOutput:
        """
        Retrieves Spaces and Makes them Searchable
        """
        if self.access_token is None:
            raise ConnectorMissingCredentialError("Hermes")

        api_client = Hermes(access_token=self.access_token)
        all_spaces = api_client.get_all_spaces()

        space_batch: list[Document] = []

        for space in all_spaces:
            updated_at = space.get("last_updated")
            if updated_at:
                updated_at = datetime.fromisoformat(updated_at)

            space_id = space.get("_id")
            space_name = space.get("name")
            created_by = space.get("created_by")
            threads = space.get("threads", [])
            searches = space.get("searches", [])

            link = f"{HERMES_URL}spaces/{space_id}"

            threads_text = '\n'.join([f"- Thread: {thread}" for thread in threads])
            searches_text = '\n'.join([f"- Search Query: {search}" for search in searches])

            context_text = (
                f"Space Name: {space_name}\n"
                f"Created By: {created_by}\n"
                f"Last Updated: {updated_at}\n"
                f"Threads:\n{threads_text}\n"
                f"Searches:\n{searches_text}\n"
            )

            space_batch.append(
                Document(
                    id=space_id,
                    sections=[Section(link=link, text=context_text)],
                    source=DocumentSource.HERMES, 
                    semantic_identifier=space_id,
                    doc_updated_at=updated_at.astimezone(timezone.utc),
                    metadata={
                        "space_name": space_name,
                        "created_by": created_by,
                        "threads": threads,
                        "searches": searches,
                        "enterprise_id": space.get("enterprise_id"),
                        "type":"space"
                    }
                )
            )

            if len(space_batch) >= self.batch_size:
                yield space_batch
                space_batch = []

        if space_batch:
            yield space_batch


    def load_from_state(self) -> GenerateDocumentsOutput:
        return self._process_messages() + self._process_spaces()
    
    def poll_source(
            self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        start_datetime = datetime.utcfromtimestamp(start)
        end_datetime = datetime.utcfromtimestamp(end)
        return self._process_messages(start_datetime, end_datetime) + self._process_spaces(start_datetime, end_datetime)
    
if __name__ == "__main__":
    import os
    
    connector = HermesConnector()
    connector.load_credentials(
        {"hermes_access_token": str(os.environ["HERMES_ACCESS_TOKEN"])}
    )
    logger.info("hermes access token is ", str(os.environ["HERMES_ACCESS_TOKEN"]))

    document_batches = connector.load_from_state()
    print(next(document_batches))
