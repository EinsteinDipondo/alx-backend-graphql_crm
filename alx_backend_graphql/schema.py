# alx_backend_graphql/schema.py
import graphene

# Define the Query class
class Query(graphene.ObjectType):
    # Define a field named 'hello' that returns a String
    hello = graphene.String(description="A simple greeting endpoint")
    
    # Resolver function for the 'hello' field
    def resolve_hello(self, info):
        return "Hello, GraphQL!"

# Create the schema
schema = graphene.Schema(query=Query)