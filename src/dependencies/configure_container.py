from src.dependencies.container import Container
from src.workflow.services.llm_service import LlmService
from src.workflow.services.prompt_service import PromptService
from src.workflow.agents.supervisor.supervisor_agent import Supervisor
from src.workflow.orchestrator.orchestrator import Orchestrator

from src.api.core.services.encryption_service import EncryptionService
from src.api.core.services.hashing_service import HashingService
from src.api.core.services.http_service import HttpService
from src.api.core.middleware.middleware_service import MiddlewareService
from src.api.core.services.request_validation_service import RequestValidationService
from src.api.modules.websocket.websocket_service import WebsocketService
from src.api.core.services.webtoken_service import WebTokenService



def configure_container():
    ## Independent ##
    encryption_service = EncryptionService()
    Container.register("encryption_service", encryption_service)

    hashing_service = HashingService()
    Container.register("hashing_service", hashing_service)

    llm_service = LlmService()
    Container.register("llm_service", llm_service)
    
    prompt_service = PromptService()
    Container.register("prompt_service", prompt_service)

    request_validation_service = RequestValidationService()
    Container.register("request_validation_service", request_validation_service)

    

    websocket_service = WebsocketService()
    Container.register("websocket_service", websocket_service)

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

    middleware_service = MiddlewareService(
        http_service=http_service
    )
    Container.register("middleware_service", middleware_service)

    orchestrator = Orchestrator(
        websocket_service=websocket_service
    )
    Container.register("orchestrator", orchestrator)

    supervisor = Supervisor(
        prompt_service=prompt_service,
        llm_service=llm_service
    )
    Container.register("supervisor", supervisor)


    




