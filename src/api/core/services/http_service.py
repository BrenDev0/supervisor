from src.api.core.services.encryption_service import EncryptionService
from src.api.core.services.hashing_service import HashingService
from src.api.core.services.request_validation_service import RequestValidationService
from src.api.core.services.webtoken_service import WebTokenService
from src.utils.logs.logger import Logger

class HttpService:
    def __init__(
        self,
        encryption_service: EncryptionService,
        logger: Logger,
        hashing_service: HashingService,
        request_validation_service: RequestValidationService,
        webtoken_service: WebTokenService 
    
    ):
        self.encryption_service: EncryptionService = encryption_service
        self.logger: Logger = logger
        self.hashing_service: HashingService = hashing_service
        self.request_validation_service: RequestValidationService = request_validation_service
        self.webtoken_service: WebTokenService = webtoken_service