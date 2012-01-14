class ApiError(Exception): pass
class PermissionError(ApiError): pass
class UnitDoesNotExist(ApiError): pass
class DuplicateObject(ApiError): pass