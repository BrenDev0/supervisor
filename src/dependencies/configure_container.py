from src.dependencies.container import Container
from src.workflow.services.embeddings_service import EmbeddingService
from src.workflow.services.llm_service import LlmService
from src.workflow.services.prompt_service import PromptService

from src.api.core.services.encryption_service import EncryptionService
from src.api.core.services.hashing_service import HashingService
from src.api.core.services.request_validation_service import RequestValidationService
from src.api.core.services.webtoken_service import WebTokenService
from src.api.core.services.http_service import HttpService


def configure_container():
    ## Independent ##
    embedding_service = EmbeddingService()
    Container.register("embedding_service", embedding_service)

    encryption_service = EncryptionService()
    Container.register("encryption_service", encryption_service)

    hashing_service = HashingService()
    Container.register("hashing_service", hashing_service)

    llm_service = LlmService()
    Container.register("llm_service", llm_service)

    request_validation_service = RequestValidationService()
    Container.register("request_validation_service", request_validation_service)

    webtoken_service = WebTokenService()
    Container.register("webtoken_service", webtoken_service)

    ##  Dependent
    http_service = HttpService(
        encryption_service=encryption_service,
        hashing_service=hashing_service,
        request_validation_service=request_validation_service,
        webtoken_service=webtoken_service
    )
    Container.register("http_service", http_service)


    prompt_service = PromptService(
        embedding_service=embedding_service
    )
    Container.register("prompt_service", prompt_service)



    




