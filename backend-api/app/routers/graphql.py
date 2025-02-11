from strawberry.fastapi import GraphQLRouter
from app.graphql.context import get_context
from app.graphql.schema import schema

router = GraphQLRouter(
    schema=schema,
    context_getter=get_context,
    graphql_ide="apollo-sandbox",
    multipart_uploads_enabled=True,  # type: ignore
)
