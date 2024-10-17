import os
import ast
import os
import json

from swarm import Agent, Swarm 

def analyze_code_from_directory(context_variables):
    directory = context_variables.get('directory', '')
    if not os.path.exists(directory):
        return f"The directory '{directory}' does not exist."

    analysis_results = []
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".py"):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    code = file.read()
                    tree = ast.parse(code)

                    class_defs = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                    function_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and not isinstance(node.parent, ast.ClassDef)]

                    classes_info = []
                    for cls in class_defs:
                        methods_info = []
                        for method in cls.body:
                            if isinstance(method, ast.FunctionDef):
                                params = [arg.arg for arg in method.args.args]
                                return_type = ast.get_docstring(method)
                                methods_info.append({
                                    'name': method.name,
                                    'parameters': params,
                                    'return_type': return_type or 'Any'
                                })
                        classes_info.append({
                            'name': cls.name,
                            'methods': methods_info
                        })

                    functions_info = []
                    for func in function_defs:
                        params = [arg.arg for arg in func.args.args]
                        return_type = ast.get_docstring(func)
                        functions_info.append({
                            'name': func.name,
                            'parameters': params,
                            'return_type': return_type or 'Any'
                        })

                    analysis_results.append({
                        'filename': filename,
                        'classes': classes_info,
                        'functions': functions_info
                    })
    return analysis_results

CodeAnalysisAgent = Agent(
    name="CodeAnalysisAgent",
    instructions=(
        "You are a highly skilled Python code analysis agent. Your task is to perform an in-depth analysis of Python source code files "
        "in the specified directory. Extract detailed information about classes, methods, functions, parameters, return types, and docstrings. "
        "Ensure that parent-child relationships are accurately captured. Return the analysis results in a structured format that can be "
        "easily consumed by other agents in the swarm."
    ),
    functions=[analyze_code_from_directory]
)

def generate_schema(context_variables):
    analysis_results = context_variables.get('analysis_results', [])
    schema = {
        'library_name': 'SimulatedLibrary',
        'classes': [],
        'functions': []
    }

    for result in analysis_results:
        for cls in result['classes']:
            class_schema = {
                'name': cls['name'],
                'methods': []
            }
            for method in cls['methods']:
                method_schema = {
                    'name': method['name'],
                    'parameters': [{'name': param} for param in method['parameters']],
                    'return_type': method['return_type']
                }
                class_schema['methods'].append(method_schema)
            schema['classes'].append(class_schema)
        
        for func in result['functions']:
            function_schema = {
                'name': func['name'],
                'parameters': [{'name': param} for param in func['parameters']],
                'return_type': func['return_type']
            }
            schema['functions'].append(function_schema)

    return json.dumps(schema, indent=2)

SchemaAgent = Agent(
    name="SchemaAgent",
    instructions=(
        "You are an expert schema generator agent. Using the detailed analysis results provided, your task is to construct a comprehensive "
        "JSON schema that accurately represents the codebase's structure. Include all relevant details such as class names, method names, "
        "function names, parameters (with names and types if available), return types, and docstrings where applicable. Ensure the schema "
        "is well-structured and formatted to facilitate seamless code generation by downstream agents."
    ),
    functions=[generate_schema]
)

def generate_code_from_schema(context_variables):
    schema_json = context_variables.get('schema_json', '')
    output_directory = context_variables.get('output_directory', 'generated_code')

    schema = json.loads(schema_json)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Generate code for classes
    for cls in schema.get('classes', []):
        class_name = cls['name']
        methods = cls.get('methods', [])
        class_code = f"class {class_name}:\n"
        if not methods:
            class_code += "    pass\n"
        else:
            for method in methods:
                method_name = method['name']
                parameters = method.get('parameters', [])
                params_str = ', '.join(['self'] + [p['name'] for p in parameters])
                # Mock implementation returning fake data
                method_code = (
                    f"    def {method_name}({params_str}):\n"
                    f"        # Simulated method\n"
                    f"        return 'Fake data for {method_name}'\n"
                )
                class_code += method_code + "\n"
        # Save the class code to a file
        file_path = os.path.join(output_directory, f"{class_name}.py")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(class_code)

    # Generate code for standalone functions
    functions = schema.get('functions', [])
    if functions:
        functions_code = ""
        for func in functions:
            function_name = func['name']
            parameters = func.get('parameters', [])
            params_str = ', '.join([p['name'] for p in parameters])
            # Mock implementation returning fake data
            function_code = (
                f"def {function_name}({params_str}):\n"
                f"    # Simulated function\n"
                f"    return 'Fake data for {function_name}'\n\n"
            )
            functions_code += function_code

        # Save functions to a file
        file_path = os.path.join(output_directory, "functions.py")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(functions_code)

    return f"Code generated successfully in the directory '{output_directory}'."

CodeAgent = Agent(
    name="CodeAgent",
    instructions=(
        "You are a proficient code generation agent. Your task is to generate Python source code files based on the provided JSON schema. "
        "For each class and function, create corresponding Python code that mirrors the original API. Implement mock methods and functions that "
        "return fake data or placeholder values, enabling developers to use the simulated library as if it were the original. Ensure that the code "
        "is syntactically correct, well-formatted, and adheres to Python coding conventions. Save all generated code files into the specified output directory."
    ),
    functions=[generate_code_from_schema]
)

def orchestrate_task(context_variables):
    client = Swarm()

    # Step 1: Analyze code
    analysis_response = client.run(
        agent=CodeAnalysisAgent,
        context_variables={'directory': context_variables.get('code_directory', '')}
    )
    analysis_results = analysis_response.content

    # Step 2: Generate schema
    schema_response = client.run(
        agent=SchemaAgent,
        context_variables={'analysis_results': analysis_results}
    )
    schema_json = schema_response.content

    # Step 3: Generate code
    code_response = client.run(
        agent=CodeAgent,
        context_variables={
            'schema_json': schema_json,
            'output_directory': context_variables.get('output_directory', 'generated_code')
        }
    )
    return code_response.content

OrchestratorAgent = Agent(
    name="OrchestratorAgent",
    instructions=(
        "You are an intelligent orchestration agent responsible for coordinating multiple agents to complete a complex task. "
        "Sequentially invoke the CodeAnalysisAgent, SchemaAgent, and CodeAgent, ensuring that each agent receives the correct inputs and "
        "that their outputs are properly passed along. Monitor the process for any errors or exceptions, and ensure the successful completion "
        "of the overall task. Provide clear and concise feedback upon task completion."
    ),
    functions=[orchestrate_task]
)

def create_agents_dynamically(context_variables):
    task = context_variables.get('task', '').lower()
    agents_needed = []

    if "analyze" in task or "analysis" in task:
        agents_needed.append("CodeAnalysisAgent")
    if "create schema" in task or "generate schema" in task:
        agents_needed.append("SchemaAgent")
    if "generate code" in task or "code generation" in task:
        agents_needed.append("CodeAgent")
    if "orchestrate" in task or "coordinate" in task:
        agents_needed.append("OrchestratorAgent")

    return f"Agents created for the task: {', '.join(agents_needed)}"

MasterAgent = Agent(
    name="MasterAgent",
    instructions=(
        "You are a master agent responsible for dynamically creating and configuring other agents based on the user's task description. "
        "Interpret the user's task carefully to determine which agents are required. Instantiate and configure the necessary agents, and prepare "
        "them for execution. Your goal is to set up the swarm effectively to accomplish the user's objectives."
    ),
    functions=[create_agents_dynamically]
)

# Initialize the Swarm client
client = Swarm()

# Path to the directory containing the source code to analyze
code_directory = 'code_directory'  # Replace with actual path

# Directory where the generated code will be saved
output_directory = 'output_directory'  # Replace with actual path

# User-provided task
user_task = "Analyze the code, create a schema, and generate a simulated library. Including all, don't forget nothing. Production code ready."

# Execute the MasterAgent to create the necessary agents
master_response = client.run(
    agent=MasterAgent,
    context_variables={'task': user_task}
)
print(master_response.content)

# Execute the OrchestratorAgent to coordinate the entire process
orchestrator_response = client.run(
    agent=OrchestratorAgent,
    context_variables={
        'code_directory': code_directory,
        'output_directory': output_directory
    }
)
print(orchestrator_response.content)
