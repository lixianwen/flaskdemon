import werkzeug
from flask_restx import Api


api = Api(
    doc='/doc'
)


@api.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400
