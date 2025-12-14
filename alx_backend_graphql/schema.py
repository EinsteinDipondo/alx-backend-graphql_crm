# alx_backend_graphql/schema.py
import graphene

# First, create a CRMQuery class
class CRMQuery(graphene.ObjectType):
    # Define a field named 'hello' that returns a String
    hello = graphene.String(description="A simple greeting endpoint")
    
    # Resolver function for the 'hello' field
    def resolve_hello(self, info):
        return "Hello, GraphQL!"

# Now create Query that inherits from CRMQuery AND graphene.ObjectType
class Query(CRMQuery, graphene.ObjectType):
    # This class inherits all fields from CRMQuery
    pass

# Create the schema
schema = graphene.Schema(query=Query)