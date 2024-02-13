from datetime import datetime
from datetime import timezone
from typing import Any

import requests
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
        self.batch_size = batch_size
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
        
        api_client = Hermes(access_token=self.access_token) #TODO: implement hermes
        message_threads = api_client.get_all_message_threads() #TODO: fetch all threads

        doc_batch: list[Document] = []

        for thread in message_threads:
            updated_at = thread.get("timestamp")
            if start is not None and updated_at < start:
                continue
            if end is not None and updated_at > end:
                continue
                
            messages = thread.get("messages")

            link = f"{HERMES_URL}threads/{thread.get('thread_id')}"

            message_texts = []

            for message in messages:
                context = f"From: {message.get('sender_username')}\n \
                            Filename: {message.get('filename')}\n \
                            Code: {message.get('code')}\n \
                            Message: {message.get('message')}"
                message_texts.append(context)

            message_text = '\n'.join(message_texts)
            context_text = f"Messages: {message_text}"

            doc_batch.append(
                Document(
                    id=thread.get("thread_id"),
                    sections=[Section(link=link, text=context_text)],
                    source=DocumentSource.HERMES, 
                    semantic_identifier=thread.get("thread_id"),
                    doc_updated_at=updated_at,
                    metadata={}
                )
            )

            if len(doc_batch) >= self.batch_size:
                yield doc_batch
                doc_batch = []
        
        if doc_batch:
            yield doc_batch


    def _process_spaces():
        """
        Retrieves Spaces and Makes them Searchable        
        """
        # TODO
        pass

    def load_from_state(self) -> GenerateDocumentsOutput:
        return self._process_messages()
    
    def poll_source(
            self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        start_datetime = datetime.utcfromtimestamp(start)
        end_datetime = datetime.utcfromtimestamp(end)
        return self._process_messages(start_datetime, end_datetime)
    
if __name__ == "__main__":
    import os
    
    connector = HermesConnector()
    connector.load_credentials(
        {"hermes_access_token": os.environ["HERMES_ACCESS_TOKEN"]}
    )

    document_batches = connector.load_from_state()
    print(next(document_batches))
