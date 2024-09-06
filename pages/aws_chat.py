import boto3
from llama_index.core.tools import FunctionTool
from llama_index.agent import OpenAIAgent
from llama_index.core.tools import ToolSelection
from datetime import datetime, timedelta

class AWSQueryTool(FunctionTool):
    """
    Custom tool to handle AWS Cost Explorer queries based on natural language input.
    """

    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name='eu-west-2'):
        self.client = boto3.client(
            'ce',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

    def parse_query(self, query):
        """
        Parse the natural language query and convert it into AWS Cost Explorer API parameters.
        """
        # A simple heuristic to detect time ranges and specific cost requests from natural language queries
        if "top instances" in query and "on-demand" in query:
            return self.get_top_instances_by_on_demand_spend()
        elif "total cost" in query and "last month" in query:
            return self.get_total_cost_for_last_month()
        else:
            return "I'm sorry, I didn't understand the query. Please ask about costs, instances, or time periods."

    def get_top_instances_by_on_demand_spend(self):
        """
        Get the top instances by on-demand spend in the last month.
        """
        end_date = datetime.now().date()
        start_date = (end_date.replace(day=1) - timedelta(days=1)).replace(day=1)

        response = self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'},
                {'Type': 'DIMENSION', 'Key': 'REGION'}
            ],
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['Amazon Elastic Compute Cloud - Compute']
                }
            }
        )

        # Extract data from the response
        results = response.get('ResultsByTime', [])[0].get('Groups', [])
        if not results:
            return "No data available for the requested period."

        result_str = "Top EC2 instances by On-Demand spend:\n"
        for group in results:
            instance_type = group['Keys'][0]
            region = group['Keys'][1]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            result_str += f"Instance Type: {instance_type}, Region: {region}, Cost: ${amount}\n"

        return result_str

    def get_total_cost_for_last_month(self):
        """
        Get the total AWS cost for the last month.
        """
        end_date = datetime.now().date()
        start_date = (end_date.replace(day=1) - timedelta(days=1)).replace(day=1)

        response = self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )

        total_cost = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        return f"Total AWS cost for last month: ${total_cost}"

    def call(self, input_text):
        """
        This method is required by LlamaIndex to call the tool with user input.
        """
        return self.parse_query(input_text)


# AWS credentials
aws_access_key_id = 'your_access_key'
aws_secret_access_key = 'your_secret_key'
region_name = 'eu-west-2'

# Instantiate the AWS Query Tool
aws_tool = AWSQueryTool(aws_access_key_id, aws_secret_access_key, region_name)

# Create a ToolSet for the agent
tools = ToolSelection([aws_tool])

# Instantiate the agent
agent = OpenAIAgent(toolsets=tools)

# Sample user query
query = "What are the top instances by on-demand spend?"
response = agent.chat(query)

print(response)
