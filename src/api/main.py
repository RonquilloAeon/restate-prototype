from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from .graphql import schema

# Create FastAPI app
app = FastAPI(title="Light Bulb Tracking System")

# Add GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Add a redirect from root to GraphQL UI
@app.get("/")
async def redirect_to_graphql():
    return {"message": "Welcome to Light Bulb Tracking System", "graphql_endpoint": "/graphql"}
