from local import LocalStack

# a singleton sentinel value for parameter defaults
_sentinel = object()

# context locals
_request_ctx_stack = LocalStack()
_app_ctx_stack = LocalStack()
