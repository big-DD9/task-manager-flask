from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)


class TaskCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    status = fields.String(
        required=False,
        validate=validate.OneOf(["pending", "in_progress", "done"])
    )


class TaskUpdateSchema(Schema):
    title = fields.String(required=False, validate=validate.Length(min=1, max=200))
    description = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    status = fields.String(
        required=False,
        validate=validate.OneOf(["pending", "in_progress", "done"])
    )
