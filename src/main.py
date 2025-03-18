import uvicorn
from fastapi import FastAPI
from restate.fastapi import restatefy
from strawberry.fastapi import GraphQLRouter

from lightbulbs.graphql import schema

# Create FastAPI app
app = FastAPI(title="Light Bulb Tracking System")

# Restatefy the app to integrate with Restate
restatefy(app)

# Add GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Add a redirect from root to GraphQL UI
@app.get("/")
async def redirect_to_graphql():
    return {"message": "Welcome to Light Bulb Tracking System", "graphql_endpoint": "/graphql"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)