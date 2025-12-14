# alx_backend_graphql/schema.py
import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(CRMQuery, graphene.ObjectType):
    # This will combine queries from crm schema
    pass


class Mutation(CRMMutation, graphene.ObjectType):
    # This will combine mutations from crm schema
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)