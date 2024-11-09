import os
import ast
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

                    functions_info = [
                        {
                            'name': node.name,
                            'parameters': [arg.arg for arg in node.args.args],
                            'return_type': ast.get_docstring(node) or 'Any'
                        }
                        for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                    ]

                    analysis_results.append({
                        'filename': filename,
                        'functions': functions_info
                    })

    return analysis_results

def generate_simulated_code(context_variables):
    analysis_results = context_variables.get('analysis_results', [])
    output_directory = context_variables.get('output_directory', 'generated_code')

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    functions_code = ""
    for result in analysis_results:
        for func in result.get('functions', []):
            function_name = func['name']
            parameters = func.get('parameters', [])
            params_str = ', '.join(parameters)
            return_type = func.get('return_type', 'Any')
            function_code = (
                f"def {function_name}({params_str}) -> {return_type}:\n"
                f"    # Simulated function\n"
                f"    print(f'Simulated {function_name} called with parameters: {{{params_str}}}')\n"
                f"    return 'Simulated result from {function_name}'\n\n"
            )
            functions_code += function_code

    file_path = os.path.join(output_directory, "simulated_library.py")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(functions_code)

    return f"Simulated code generated successfully in the file '{file_path}'."

CodeAnalysisAgent = Agent(
    name="CodeAnalysisAgent",
    instructions="Analyze Python source code files in the specified directory.",
    functions=[analyze_code_from_directory]
)

SimulatedCodeAgent = Agent(
    name="SimulatedCodeAgent",
    instructions="Generate simulated Python code based on the provided code analysis results.",
    functions=[generate_simulated_code]
)

def orchestrate_task(context_variables):
    client = Swarm()

    # Step 1: Analyze code
    analysis_response = client.run(
        agent=CodeAnalysisAgent,
        messages=[{"role": "system", "content": "Analyze the code in the specified directory."}],
        context_variables={'directory': context_variables.get('code_directory', '')}
    )
    analysis_results = analysis_response.messages[-1]["content"]
    print(f"Analysis completed: {analysis_results}")

    # Step 2: Generate simulated code
    code_response = client.run(
        agent=SimulatedCodeAgent,
        messages=[{"role": "system", "content": "Generate real python code based on the analysis results. Show only code, no explication."}],
        context_variables={
            'analysis_results': analysis_results,
            'output_directory': context_variables.get('output_directory', 'generated_code')
        }
    )

    return code_response.messages[-1]["content"]

OrchestratorAgent = Agent(
    name="OrchestratorAgent",
    instructions="Coordinate the code analysis and simulated code generation process.",
    functions=[orchestrate_task]
)

# Usage
if __name__ == "__main__":
    client = Swarm()
    code_directory = 'C:\\Users\\admlocal\\Documents\\POC\\swarm_simulation_tool\\code_directory'
    output_directory = 'C:\\Users\\admlocal\\Documents\\POC\\swarm_simulation_tool\\generated_code'

    try:
        result = client.run(
            agent=OrchestratorAgent,
            messages=[{"role": "system", "content": "Orchestrate the task with analysis and simulated code generation."}],
            context_variables={
                'code_directory': code_directory,
                'output_directory': output_directory
            }
        )
        print(result)
    except Exception as e:
        print(f"An error occurred: {str(e)}")